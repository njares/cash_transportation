import sys
import os
import itertools
from scipy.special import comb
import numpy as np
import pandas as pd
import time

sys.path.append('../solverpulp')
import model

def calculo_recaudaciones(prop_suc, collections, e_zero, buzones):
	# ToDo: propagar prop_suc
	return collections, e_zero, buzones

def calculo_ganancia(business_days, rutas, costos_rutas, interes, prop_suc, collections, e_zero, buzones, n_thr=4, solver='cbc', debug=False):
	data_dir = './data/'

	# Dias habiles por ruta
	habiles_csv_path = os.path.join(data_dir, "habiles.csv")
	business_days.to_csv(habiles_csv_path, header=False, index=False)

	# Datos de rutas
	rutas_csv_path = os.path.join(data_dir, "rutas.csv")
	rutas.to_csv(rutas_csv_path, header=False, index=False)

	# Costos por ruta
	costo_rutas_csv_path = os.path.join(data_dir, "costo_rutas.csv")
	costos_rutas.to_csv(costo_rutas_csv_path, header=False, index=False)

	collections, e_zero, buzones = calculo_recaudaciones(prop_suc, collections, e_zero, buzones)

	# Recaudaciones por sucursal
	recaudacion_csv_path = os.path.join(data_dir, "recaudacion.csv")
	collections.to_csv(recaudacion_csv_path, header=False, index=False, sep="\t")

	# Recaudacion inicial
	e_zero_csv_path = os.path.join(data_dir, "e0.csv")
	e_zero.to_csv(e_zero_csv_path, header=False, index=False)

	# Datos de buzones
	buzones_csv_path = os.path.join(data_dir, "buzon.csv")
	buzones.to_csv(buzones_csv_path, header=False, index=False)

	_,n_d = business_days.shape
	n_p,n_s = rutas.shape

	# Calcular con costo financiero
	status, variables, Problems = model.model_problem(
		n_d, n_s, n_p,
		rutas_csv_path, costo_rutas_csv_path, e_zero_csv_path,
		buzones_csv_path, habiles_csv_path, recaudacion_csv_path,
		daily_interest_rate=interes,n_thr=n_thr,solver=solver,debug=debug
	)
	try:
		costos_total_caso_financiero = sum([prob.objective.value() for prob in Problems])
	except:
		return -1

	# Calcular sin costo financiero
	status, variables, Problems = model.model_problem(
		n_d, n_s, n_p,
		rutas_csv_path, costo_rutas_csv_path, e_zero_csv_path,
		buzones_csv_path, habiles_csv_path, recaudacion_csv_path,
		daily_interest_rate=0.0,n_thr=n_thr,solver=solver,debug=debug
	)
	try:
		costos_logístico_sin_financiero = sum([prob.objective.value() for prob in Problems])
	except:
		return -1

	# Calcular costo financiero del caso logístico
	costos_financiero_logístico = e_zero.values.sum()
	for var in variables:
		var_id = var.name.split('_')[0]
		if var_id == 'e':
			suc,dia = var.name.split('_')[1:]
			if dia != n_d-1:
				costos_financiero_logístico += var.varValue
	costos_financiero_logístico *= interes

	costos_total_caso_logistico = costos_financiero_logístico + costos_logístico_sin_financiero

	ganancia = (costos_total_caso_logistico - costos_total_caso_financiero) / costos_total_caso_logistico

	return ganancia

def generar_escenarios(n_s,n_p,n):
	cant_rutas_posibles = 2**n_s - n_s - 1
	cant_rutas_elegir = n_p - n_s
	# Generar la lista de números que determinan cada ruta no trivial
	rutas_posibles = list(range(2**n_s))
	rutas_posibles.remove(0)
	for i in range(n_s):
		rutas_posibles.remove(2**i)
	# Generar listas de tamaño n_p-n_s de índices de esa lista
	escenarios_posibles = itertools.combinations(range(cant_rutas_posibles),cant_rutas_elegir)
	# Elegir n de esas listas
	N = int(comb(cant_rutas_posibles,cant_rutas_elegir))
	indices_escenarios = np.random.choice(N,n,replace=False)
	r = iter(range(N))
	# filter
	indices_rutas = [next(escenarios_posibles) for _ in range(N) if next(r) in indices_escenarios]
	# Generar las rutas
	escenarios = []
	fmt_str = "{:0"+str(n_s)+"b}"
	for indices in indices_rutas:
		rutas = [rutas_posibles[i] for i in indices]
		rutas = [fmt_str.format(ruta) for ruta in rutas]
		rutas = [list(map(int,ruta)) for ruta in rutas]
		rutas = np.vstack([np.eye(n_s),rutas])
		rutas = pd.DataFrame(rutas)
		escenarios.append(rutas)
	return escenarios

def agregar_resultado(exp_dict, collections_profiles, std_profiles, n_thr, solver, debug=False):
	data_dir = './data/'
	rutas_csv_path = os.path.join(data_dir, "rutas.csv")
	costo_rutas_csv_path = os.path.join(data_dir, "costo_rutas.csv")
	habiles_csv_path = os.path.join(data_dir, "habiles.csv")
	# generar semilla
	rand_seed = len(exp_dict)
	exp_dict[rand_seed] = {}
	# generar perfiles aleatorios
	rng = np.random.default_rng(seed=rand_seed)
	profiles_names = ["constant", "V"]
	for collections,std,name in zip(collections_profiles,std_profiles, profiles_names):
		n_s,n_d = collections.shape
		#n_p,_ = rutas.shape
		n_p = 8
		e_zero = collections[:,0]
		rand_collect = rng.normal(loc=0.0,scale=std,size=collections.shape)
		rand_e_zero = rng.normal(loc=0,scale=std,size=e_zero.shape)
		# la std constante es 52% de la recaudación diaria
		# 1.9 asegura no tener recaudaciones negativas
		rand_collect = np.clip(rand_collect,-1.9*std,1.9*std)
		rand_e_zero = np.clip(rand_e_zero,-1.9*std,1.9*std)
		collections = collections + rand_collect
		e_zero = e_zero + rand_e_zero
		e_zero = pd.DataFrame(e_zero)
		collections = pd.DataFrame(collections)
		# guardar perfiles aleatorios
		# Recaudaciones por sucursal
		recaudacion_csv_path = os.path.join(data_dir, "recaudacion.csv")
		collections.to_csv(recaudacion_csv_path, header=False, index=False, sep="\t")
		# Recaudacion inicial
		e_zero_csv_path = os.path.join(data_dir, "e0.csv")
		e_zero.to_csv(e_zero_csv_path, header=False, index=False)
		exp_dict[rand_seed][name] = {}
		for interes_anual in np.linspace(0,10,11):
			interes = (1+interes_anual/100)**(1/365)-1
			exp_dict[rand_seed][name][interes_anual] = {}
			#cantidad de recolecciones mensuales
			for b in range(4):
				buzones = np.ones(n_s) / (b+1)
				buzones = pd.DataFrame(buzones)
				# Datos de buzones
				buzones_csv_path = os.path.join(data_dir, "buzon.csv")
				buzones.to_csv(buzones_csv_path, header=False, index=False)
				print(f"Resolviendo caso {rand_seed} {name} {interes_anual} {b} ", end="")
				start = time.time()
				# Resolver problema
				status, variables, Problems = model.model_problem(
					n_d, n_s, n_p,
					rutas_csv_path, costo_rutas_csv_path, e_zero_csv_path,
					buzones_csv_path, habiles_csv_path, recaudacion_csv_path,
					daily_interest_rate=interes,n_thr=n_thr,solver=solver,debug=debug
				)
				tiempo = time.time()-start
				print(f"t={tiempo:.2f}")
				# import pdb;
				# pdb.set_trace()
				try:
					# Calcular costo total
					costo_total = sum([prob.objective.value() for prob in Problems])
					# Calcular costo financiero sin interés
					costo_financiero = e_zero.values.sum()
					for var in variables:
						var_id = var.name.split('_')[0]
						if var_id == 'e':
							_, dia = var.name.split('_')[1:]
							if int(dia) != n_d-1:
								costo_financiero += var.varValue
					# es sin interés, porque para el costo financiero real
					# se necesita la siguiente linea:
					# costos_financiero_logístico *= interes
				except:
					import pdb;
					pdb.set_trace()
					return -1
				exp_dict[rand_seed][name][interes_anual][b] = [costo_total, costo_financiero]
	return exp_dict

# Llaves:
#	- rand_seed (1)
#		- perfil (2)
#			- interés (11) [0,1,2,3,4,5,6,7,8,9,10]
#				- buzón (4)

# Values:
#	- costo total
#	- costo financiero sin interés
