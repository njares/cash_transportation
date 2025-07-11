import numpy as np
import pandas as pd
import sys
import time
from helpers import *
import json

n_thr = 16

# ~ try:
	# ~ with open('rutas_exploradas.json','r',encoding='utf-8') as f:
		# ~ rutas_exploradas = json.load(f)
# ~ except FileNotFoundError:
	# ~ rutas_exploradas = {}
rutas_exploradas = {}

# Llaves:
# - número de sucursales
# - número de rutas
# - matriz de rutas

dias_habiles_profile = [1,1,1,1,1,0,0]*4+[1,1]

collections_profile = np.ones(30)

for n_s in range(3,4):
	if str(n_s) not in rutas_exploradas.keys():
		rutas_exploradas[str(n_s)] = {}
	prop_suc = np.ones(n_s)
	e_zero = np.ones(n_s)
	collections = np.tile(collections_profile,(n_s,1))
	buzones = collections.sum(1) / 3
	prop_suc = pd.DataFrame(prop_suc)
	e_zero = pd.DataFrame(e_zero)
	collections = pd.DataFrame(collections)
	buzones = pd.DataFrame(buzones)
	for n_p in range(n_s+1,n_s+2):# 2*n_s+1):
		if str(n_p) not in rutas_exploradas[str(n_s)].keys():
			rutas_exploradas[str(n_s)][str(n_p)] = {}
		dias_habiles = np.tile(dias_habiles_profile,(n_p,1))
		costos_rutas = np.ones(n_p)
		dias_habiles = pd.DataFrame(dias_habiles)
		costos_rutas = pd.DataFrame(costos_rutas)
		escenarios = generar_escenarios(n_s,n_p,4)
		n_i=1
		for rutas in escenarios:
			rutas_key = repr(rutas.values.tolist())
			if rutas_key not in rutas_exploradas[str(n_s)][str(n_p)].keys():
				rutas_exploradas[str(n_s)][str(n_p)][rutas_key] = {}
				interes = (1+40/100)**(1/365)-1
				print("Resolviendo caso {} {} {}... ".format(n_s,n_p,n_i),end='')
				sys.stdout.flush()
				start = time.time()
				# Calcular ganancia
				ganancia = calculo_ganancia(dias_habiles, rutas, costos_rutas, interes, prop_suc, collections, e_zero, buzones, n_thr=n_thr, scip=True)
				tiempo = time.time()-start
				print("ganancia={} t={:.2f}".format(ganancia,tiempo))
				sys.stdout.flush()
				# Guardar resultado en el diccionario
				rutas_exploradas[str(n_s)][str(n_p)][rutas_key]['default'] = [ganancia,tiempo]
			n_i+=1

		# ~ with open('rutas_exploradas.json','w+',encoding='utf-8') as f:
			# ~ json.dump(rutas_exploradas,f)

for n_s in rutas_exploradas.keys():
	print(n_s)
	for n_p in rutas_exploradas[n_s].keys():
		print('  '+n_p)
		for rut in rutas_exploradas[n_s][n_p].keys():
			dat=' '.join(map(str,rutas_exploradas[n_s][n_p][rut]['default']))
			print(' '*4+dat)
			for row in np.array(eval(rut),dtype=int):
				print(' '*6+repr(row.tolist()))
