import configparser
import os
import pandas as pd
import sys
import time
import numpy as np

def main():
	USO = '''Uso:
	python3 main.py
	python3 main.py <archivo_configuracion>
	python3 main.py <archivo_configuracion> <modo>
	python3 main.py <archivo_configuracion> <modo> <num_threads>

	<archivo_configuracion> : ruta a un archivo de configuración válido, por defecto: ./configure.txt
	<modo> : { default | debug }
	<num_threads> : entero, cantidad de hilos de ejecución
	'''

	TAGS = {'default':[],'debug':[]}
	DEFAULT = {
		'data_dir': './data',
		'input_excel': 'DatosEntrada.xlsx',
		'output_excel': 'Plan.xlsx',
		'ignore': []
	}

	# leer configuración desde arg o defaultear a ./

	if len(sys.argv)>1:
		config_file=sys.argv[1]
	else:
		config_file='./configure.txt'

	num_thr = 4
	if len(sys.argv)>3:
		num_thr = int(sys.argv[3])

	config = configparser.ConfigParser()

	if os.path.isfile(config_file):
		try:
			config_file = config.read(config_file)
		except Exception as e:
			print("Archivo de configuración inválido: {}".format(e))
			print(USO)
			sys.exit()

		if len(sys.argv) > 2:
			tag = sys.argv[2]
		else:
			tag = 'default'

		if tag not in TAGS.keys():
			print("Modo desconocido")
			print(USO)
			sys.exit()
		else:
			data_dir = config[tag]['data_dir']
			input_excel = config[tag]['input_excel']
			output_excel = config[tag]['output_excel']
			ignore = config[tag]['ignore'].split(',')
	else:
		tag = 'default'
		# DEFAULT CONFIGURATIONS
		data_dir = DEFAULT['data_dir']
		input_excel = DEFAULT['input_excel']
		output_excel = DEFAULT['output_excel']
		ignore = DEFAULT['ignore']

	# Leer datos del excel

	input_excel_path = os.path.join(data_dir,input_excel)

	df = pd.read_excel(input_excel_path,sheet_name=None)

	# Nombres de las hojas
	sheets_name = list(df.keys())

	infogral = df[sheets_name.pop(0)]
	recaudaciones = df[sheets_name.pop(0)]
	
	if tag == 'debug':
		sheets_name = [sheet for sheet in sheets_name if sheet not in ignore]

	# obtener tasa
	daily_rate = (1 + float(infogral.columns[14]) / 100) ** (1 / 365) - 1
	extra_box = float(infogral.columns[16]) / 100

	salida = {}
	totales = {}

	all_solved = True
	
	for sheet in sheets_name:
		# generar todos los csv
		n_d, n_p, n_s, big_M, nombres, costs, e_zero, l_d_c, nombres_rutas = generate_csvs(df, sheet, data_dir)
		route_branches_csv = os.path.join(data_dir, "rutas.csv")
		cost_routes_csv = os.path.join(data_dir, "costo_rutas.csv")
		cash_in_branch_csv = os.path.join(data_dir, "e0.csv")
		box_amounts_csv = os.path.join(data_dir, "buzon.csv")
		business_days_csv = os.path.join(data_dir, "habiles.csv")
		collection_csv = os.path.join(data_dir, "recaudacion.csv")
		print("Resolviendo grupo {} ({}/{})...".format(sheet,sheets_name.index(sheet)+1,len(sheets_name)),end='')
		sys.stdout.flush()
		start = time.time()
		# correr el modelo
		status, variables = model.model_problem(
			n_d, n_s, n_p,
			route_branches_csv, cost_routes_csv, cash_in_branch_csv,
			box_amounts_csv, business_days_csv, collection_csv,
			last_days_collection=l_d_c, extra_box_percent=extra_box, daily_interest_rate=daily_rate,
			debug=False, scip=False, n_thr=num_thr
		)
		if not (all_solved and all([s=='Resuelto' for s in status])):
			all_solved = False
		print("Terminado! Tiempo transcurrido: {:.2f} s. Estado: {}".format(time.time()-start, status))
		# parsear la salida
		salida[sheet] = {}
		salida[sheet]['params'] = [n_d,n_s,nombres,status]
		salida[sheet]['rutas'] = nombres_rutas
		for var in variables:
			var_id = var.name.split('_')[0]
			if var_id == 't' and var.varValue > 0:
				suc,dia,ruta = var.name.split('_')[1:]
				if dia not in salida[sheet].keys():
					salida[sheet][dia] = {}
				if suc not in salida[sheet][dia].keys():
					salida[sheet][dia][suc] = []
				salida[sheet][dia][suc].append(ruta)

				suc_key = sheet+'-'+suc
				if suc_key not in totales.keys():
					totales[suc_key]={}
					totales[suc_key]['recaudacion'] = 0
					totales[suc_key]['paradas'] = 0
					totales[suc_key]['logístico'] = 0
					totales[suc_key]['financiero'] = e_zero[int(suc)+28]
				totales[suc_key]['recaudacion'] += var.varValue
				totales[suc_key]['paradas']+=1
				totales[suc_key]['logístico'] += costs[int(ruta)+2]
			elif var_id == 'e':
				suc,dia = var.name.split('_')[1:]
				suc_key = sheet+'-'+suc
				if suc_key not in totales.keys():
					totales[suc_key]={}
					totales[suc_key]['recaudacion'] = 0
					totales[suc_key]['paradas'] = 0
					totales[suc_key]['logístico'] = 0
					totales[suc_key]['financiero'] = e_zero[int(suc)+28]
				if dia != n_d-1:
					totales[suc_key]['financiero'] += var.varValue

	if not all_solved:
		print("Algunos problemas no fueron resueltos, revisar el log para más detalles")
	else:
		print("Todos los problemas fueron resueltos")

	# leer parámetros de función milaje
	# Fm : Abono Fijo de Milaje
	# Ru : Recaudacion de Umbral
	# mu : Coefeiciente de Excedente

	Fm = infogral.columns[12]
	Ru, mu = infogral.iloc[0:2,12]

	# sumar las recaudaciónes de todas las sucursales
	R = 0
	for suc in totales.keys():
		R += totales[suc]['recaudacion']

	# calcular la función de milaje
	Cm = Fm + max(0,mu*(R-Ru))

	# prorratearla entre las sucursales
	for suc in totales.keys():
		totales[suc]['milaje_prop'] = Cm * totales[suc]['recaudacion'] / R

	# leer parámetros de costos
	costo_parada = infogral.columns[10]
	costo_km = infogral.columns[8]
	day_names = recaudaciones.columns[3:]
	day_numbers = recaudaciones.iloc[0, 3:].dt.strftime('%d-%B') #.date.values # strftime('%d-%m')

	# Generar un excel para devolver
	ts = time.strftime('-%Y%m%d%H%M%S')
	output_excel = output_excel.split('.')
	output_excel[0] += ts
	output_excel = '.'.join(output_excel)
	output_excel_path = os.path.join(data_dir,output_excel)
	writer = pd.ExcelWriter(output_excel_path)

	for sheet in sheets_name:
		n_d = salida[sheet]['params'][0]
		n_s = salida[sheet]['params'][1]
		status_list = salida[sheet]['params'][3]
		filas = n_d + 11
		cols = n_s + 2
		hoja = np.array([['']*cols]*filas,dtype='object')
		hoja[0,2] = 'Sucursales'
		hoja[1,0] = 'Fecha'
		hoja[1,1] = 'Día'
		for i in range(n_s):
			hoja[1,2+i] = salida[sheet]['params'][2][i]
		for i in range(n_d):
			hoja[2+i,0] = day_numbers[i]
			hoja[2+i,1] = day_names[i].split(".")[0]
			# salida[sheet][dia][suc] :  lista de rutas
			if str(i) in salida[sheet].keys():
				dia = str(i)
				for j in range(n_s):
					if str(j) in salida[sheet][dia].keys():
						suc = str(j)
						rutas_str = [salida[sheet]['rutas'][int(ruta)+2] for ruta in salida[sheet][dia][suc]]
						rutas_str = map(str,rutas_str)
						hoja[2+i,2+j] = ', '.join(rutas_str)
					if not (status_list == ["Resuelto"] or (len(status_list) > 1 and status_list[j] == "Resuelto")):
						hoja[2+i,2+j] = 'N/A'
					
					
		hoja[n_d+3,0] = 'Costo de milaje prorrateado'
		hoja[n_d+4,0] = 'Costo de paradas'
		hoja[n_d+5,0] = 'Costo por kilómetros'
		hoja[n_d+7,0] = 'Costo Logístico'
		hoja[n_d+8,0] = 'Costo Financiero'
		hoja[n_d+10,0] = 'Costo Total'
		for i in range(n_s):
			if not (status_list == ["Resuelto"] or (len(status_list) > 1 and status_list[i] == "Resuelto")):
				hoja[n_d+3,2+i] = 'N/A'
				hoja[n_d+4,2+i] = 'N/A'
				hoja[n_d+5,2+i] = 'N/A'
				hoja[n_d+7,2+i] = 'N/A'
				hoja[n_d+8,2+i] = 'N/A'
				hoja[n_d+10,2+i] = 'N/A'
			else:
				suc = str(i)
				suc_key = sheet+'-'+suc
				hoja[n_d+3,2+i] = totales[suc_key]['milaje_prop']
				hoja[n_d+4,2+i] = totales[suc_key]['paradas'] * costo_parada
				hoja[n_d+5,2+i] = totales[suc_key]['logístico'] - hoja[n_d+4,2+i]
				hoja[n_d+7,2+i] = totales[suc_key]['logístico']
				hoja[n_d+8,2+i] = totales[suc_key]['financiero'] * daily_rate
				hoja[n_d+10,2+i] = hoja[n_d+7,2+i] + hoja[n_d+8,2+i]

		df = pd.DataFrame(hoja)
		df.to_excel(writer, sheet_name=sheet, float_format="%.2f",header=False, index=False)
	writer.save()

if __name__ == '__main__':
	os.chdir(os.path.realpath(sys.path[0]))
	from helpers import generate_csvs
	sys.path.append('../solverpulp')
	import model
	main()

