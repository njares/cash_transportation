import numpy as np
import pandas as pd
import sys
import time
from helpers import *
import json

n_thr = 16

# try:
# 	with open('rutas_exploradas.json','r',encoding='utf-8') as f:
# 		rutas_exploradas = json.load(f)
# except FileNotFoundError:
# 	rutas_exploradas = {}

# Llaves:
# - número de sucursales
# - número de rutas
# - matriz de rutas
# - capacidad de buzones

# Cosas fijas
n_s = 4 # número de sucursales
n_p = 8 # número de rutas
# matriz de rutas
rutas_key = '[\
[1.0, 0.0, 0.0, 0.0], \
[0.0, 1.0, 0.0, 0.0], \
[0.0, 0.0, 1.0, 0.0], \
[0.0, 0.0, 0.0, 1.0], \
[0.0, 0.0, 1.0, 1.0], \
[0.0, 1.0, 0.0, 1.0], \
[1.0, 0.0, 0.0, 1.0], \
[1.0, 1.0, 1.0, 1.0]]'
rutas = np.array(eval(rutas_key))
rutas = pd.DataFrame(rutas)
# costos de rutas
#	- Elegirlos de manera que reflejen la idea de distancia en el grafo elegido. 
# Grafo
#	    ----A---B
#	  /   / | /
#	R---D---C
# Distancias
#	{A}			R-A-R				2*(1+np.sqrt(2))
#	{B}			R-A-B-A-R			2*(2+np.sqrt(2))
#	{C}			R-D-C-D-R			4
#	{D}			R-D-R				2
#	{C,D}		R-D-C-D-R			4
#	{B,D}		R-D-C-B-C-D-R		2*(2+np.sqrt(2))
#	{A,D}		R-D-A-R				2*(1+np.sqrt(2))
#	{A,B,C,D}	R-D-C-B-A-R			2*(2+np.sqrt(2))

costos_rutas = np.array([\
2*(1+np.sqrt(2)),\
2*(2+np.sqrt(2)),\
4               ,\
2               ,\
4               ,\
2*(2+np.sqrt(2)),\
2*(1+np.sqrt(2)),\
2*(2+np.sqrt(2))\
])

#	El orden de magnitud para el caso naranja fue:
#		1.5e-03 = (total costo logisticio mensual) / (total recaudacion mensual)
# (total recaudacion mensual) = 1

costos_rutas = costos_rutas * 1.5e-3 / (4 * np.average(costos_rutas))

costos_rutas = pd.DataFrame(costos_rutas)

# días hábiles
dias_habiles_profile = [1,1,1,1,1,0,0]*4+[1,1]
dias_habiles = np.tile(dias_habiles_profile,(n_p,1))
dias_habiles = pd.DataFrame(dias_habiles)

prop_suc = np.ones(n_s)
prop_suc = pd.DataFrame(prop_suc)

# Cosas variables
# - perfil de recaudación
#	- dos perfiles: constante y con un pico
# - capacidad de buzones: ajustar para diferentes cantidades de retiros mensuales: 1, 2, 3, etc

collections_profile_constant = np.ones(30)
collections_profile_constant /= np.sum(collections_profile_constant)
collections_constant = np.tile(collections_profile_constant,(n_s,1))

# ver varianza_diaria.py
constant_std = 0.025

collections_profile_V = np.hstack([np.linspace(1,2,10,endpoint=False),np.linspace(2,1,20,endpoint=False)])
collections_profile_V /= np.sum(collections_profile_V)
collections_V = np.tile(collections_profile_V,(n_s,1))

# ver varianza diaria.py
V_std = 0.01640

collections_profiles = [collections_constant,collections_V]
std_profiles = [constant_std, V_std]

k = 1

Ganancias = []
Tiempos = []

# interes
# 	- Una vez que tengamos el esquema de trabajo acordado, hay que bajarlo hasta detectar el umbral a partir del cual la 
#		inclusión de costo financiero no es relevante.
# interes = (1+40/100)**(1/365)-1

N = 100

for i in range(N):
	for interes_anual in [0.5,1,1.5,2,2.5,3,3.5,4.0,4.5]:
		interes = (1+interes_anual/100)**(1/365)-1
		for collections,std in zip(collections_profiles,std_profiles):
			e_zero = collections[:,0]
			rand_collect = np.random.normal(loc=0.0,scale=std,size=collections.shape)
			rand_e_zero = np.random.normal(loc=0,scale=std,size=e_zero.shape)
			# la std constante es 52% de la recaudación diaria
			# 1.9 asegura no tener recaudaciones negativas
			rand_collect = np.clip(rand_collect,-1.9*std,1.9*std)
			rand_e_zero = np.clip(rand_e_zero,-1.9*std,1.9*std)
			collections = collections + rand_collect
			e_zero = e_zero + rand_e_zero
			e_zero = pd.DataFrame(e_zero)
			collections = pd.DataFrame(collections)
			for b in range(4): #cantidad de recolecciones mensuales
				buzones = np.ones(n_s) / (b+1)
				buzones = pd.DataFrame(buzones)
				
				print("Resolviendo caso {}/{}... ".format(k,2*4*N*9),end='')
				sys.stdout.flush()
				start = time.time()
				# Calcular ganancia
				ganancia = calculo_ganancia(dias_habiles, rutas, costos_rutas, interes, prop_suc, collections, e_zero, buzones, n_thr=n_thr, solver='fscip', debug=False)
				tiempo = time.time()-start
				print("ganancia={} t={:.2f}".format(ganancia,tiempo))
				sys.stdout.flush()
				k += 1
				Ganancias.append(ganancia)
				Tiempos.append(tiempo)

Ganancias = np.array(Ganancias)
Tiempos = np.array(Tiempos)

Ganancias = Ganancias.reshape(N,9,8)
Tiempos = Tiempos.reshape(N,9,8)

for i in range(9): # bucle sobre los intereses
	for j in range(8): # bucle sobre los casos
		ganancia = Ganancias[:,i,j]
		ganancia = ganancia[Ganancias[:,i,j]!=-1]
		# tiempo = Tiempos[:,i,j]
		# tiempo = tiempo[Ganancias[:,i,j]!=-1]
		
		mean_Ganancias = np.mean(ganancia)
		# mean_Tiempos = np.mean(tiempo)
		std_Ganancias = np.std(ganancia)
		# std_Tiempos = np.std(tiempo)
		print("{:.2f}+-{:.2f}".format(mean_Ganancias,std_Ganancias),end=' ')
	print("")

# ~ if str(n_p) not in rutas_exploradas[str(n_s)].keys():
	# ~ rutas_exploradas[str(n_s)][str(n_p)] = {}

# ~ if rutas_key not in rutas_exploradas[str(n_s)][str(n_p)].keys():
	# ~ rutas_exploradas[str(n_s)][str(n_p)][rutas_key] = {}

	# ~ # Guardar resultado en el diccionario
	# ~ rutas_exploradas[str(n_s)][str(n_p)][rutas_key]['default'] = [ganancia,tiempo]

	# ~ with open('rutas_exploradas.json','w+',encoding='utf-8') as f:
		# ~ json.dump(rutas_exploradas,f)

# ~ print(n_s)
# ~ print('  '+str(n_p))
# ~ dat=' '.join(map(str,rutas_exploradas[str(n_s)][str(n_p)][rutas_key]['default']))
# ~ print(' '*4+dat)
# ~ for row in np.array(eval(rutas_key),dtype=int):
	# ~ print(' '*6+repr(row.tolist()))

# ~ print(n_s)
# ~ print('  '+str(n_p))
# ~ dat=' '.join(map(str,rutas_exploradas[str(n_s)][str(n_p)][rutas_key][buzones_key]['default']))
# ~ print(' '*4+dat)
# ~ for row in np.array(eval(rutas_key),dtype=int):
	# ~ print(' '*6+repr(row.tolist()))

# ~ for n_s in rutas_exploradas.keys():
	# ~ print(n_s)
	# ~ for n_p in rutas_exploradas[n_s].keys():
		# ~ print('  '+n_p)
		# ~ for rut in rutas_exploradas[n_s][n_p].keys():
			# ~ dat=' '.join(map(str,rutas_exploradas[n_s][n_p][rut]['default']))
			# ~ print(' '*4+dat)
			# ~ for row in np.array(eval(rut),dtype=int):
				# ~ print(' '*6+repr(row.tolist()))
