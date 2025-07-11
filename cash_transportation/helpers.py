import sys
import os
import itertools
from scipy.special import comb
import numpy as np
import pandas as pd

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

