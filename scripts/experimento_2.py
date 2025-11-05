import numpy as np
import pandas as pd
import sys
import os as _os
# Ensure 'src' is on sys.path so 'cash_transportation' is importable without installation
_repo_root = _os.path.dirname(_os.path.abspath(__file__))
_repo_root = _os.path.dirname(_repo_root)
_src_path = _os.path.join(_repo_root, "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
from cash_transportation.helpers import *
import json
import argparse
import os
import time

########################################################################
# Parámetros configurables (via CLI)

parser = argparse.ArgumentParser(description="Experimento 2 - corridas con distintos perfiles/solvers")
parser.add_argument("--threads", type=int, default=8, help="cantidad de hilos")
parser.add_argument("--n-min", type=int, default=1, help="mínimo de iteraciones por escenario")
parser.add_argument("--n-max", type=int, default=0, help="máximo de iteraciones por escenario (0 = sin tope)")
parser.add_argument("--solver", type=str, default="HiGHS", help="solver a utilizar (ej. HiGHS, fscip)")
parser.add_argument("--collection-mult", type=float, default=1.0, help="multiplicador de recaudación total")
parser.add_argument("--exp-id", type=str, default="exp_test.json", help="archivo JSON del experimento (nombre simple se guarda en experiments/runs)")
parser.add_argument("--data-dir", type=str, default="./data/generated/", help="directorio donde escribir CSVs de entrada generados")
args = parser.parse_args()

n_thr = args.threads
N_min = args.n_min
N_max = args.n_max
solver = args.solver
COLLECTION_MULT = args.collection_mult
exp_id = args.exp_id
if os.path.sep not in exp_id and not exp_id.startswith('/'):
    # guardar por defecto en experiments/runs si es un nombre simple
    exp_id = os.path.join(_repo_root, 'experiments', 'runs', exp_id)
exp_dir = os.path.dirname(exp_id)
if exp_dir:
    os.makedirs(exp_dir, exist_ok=True)
if not os.path.exists(exp_id):
    with open(exp_id, 'w', encoding='utf-8') as _f:
        json.dump({}, _f)

########################################################################
# Parámetros fijos

n_s = 4 # número de sucursales
n_p = 8 # número de rutas
# matriz de rutas
rutas = np.array([\
[1.0, 0.0, 0.0, 0.0], \
[0.0, 1.0, 0.0, 0.0], \
[0.0, 0.0, 1.0, 0.0], \
[0.0, 0.0, 0.0, 1.0], \
[0.0, 0.0, 1.0, 1.0], \
[0.0, 1.0, 0.0, 1.0], \
[1.0, 0.0, 0.0, 1.0], \
[1.0, 1.0, 1.0, 1.0] \
])
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

costos_rutas = COLLECTION_MULT*costos_rutas * 1.5e-3 / (4 * np.average(costos_rutas))
costos_rutas = pd.DataFrame(costos_rutas)

# días hábiles
dias_habiles_profile = [1,1,1,1,1,1,0]*4+[1,1]
dias_habiles = np.tile(dias_habiles_profile,(n_p,1))
dias_habiles = pd.DataFrame(dias_habiles)

# ToDo: parámetro que se usa si no todas las sucursales tienen los mismos totales de recaudación
prop_suc = np.ones(n_s)
prop_suc = pd.DataFrame(prop_suc)

# - perfil de recaudación
#	- dos perfiles: constante y con un pico

#collections_profile_constant = np.ones(30)
collections_profile_constant = np.array(dias_habiles_profile)
collections_profile_constant = collections_profile_constant / np.sum(collections_profile_constant)
collections_constant = np.tile(collections_profile_constant,(n_s,1))*COLLECTION_MULT

# ver varianza_diaria.py
#constant_std = 0.025
#constant_std = (1/30)*.525
constant_std = collections_profile_constant[0]*.525*COLLECTION_MULT

collections_profile_V = np.hstack([np.linspace(1,2,10,endpoint=False),np.linspace(2,1,20,endpoint=False)])
collections_profile_V = collections_profile_V*np.array(dias_habiles_profile)
collections_profile_V /= np.sum(collections_profile_V)
collections_V = np.tile(collections_profile_V,(n_s,1))*COLLECTION_MULT

# ver varianza diaria.py
#V_std = 0.01640
#V_std = (1/30)*.3444
V_std = collections_profile_constant[0]*.3444*COLLECTION_MULT

collections_profiles = [collections_constant,collections_V]
std_profiles = [constant_std, V_std]

data_dir = args.data_dir
os.makedirs(data_dir, exist_ok=True)

# Dias habiles por ruta
habiles_csv_path = os.path.join(data_dir, "habiles.csv")
dias_habiles.to_csv(habiles_csv_path, header=False, index=False)

# Datos de rutas
rutas_csv_path = os.path.join(data_dir, "rutas.csv")
rutas.to_csv(rutas_csv_path, header=False, index=False)

# Costos por ruta
costo_rutas_csv_path = os.path.join(data_dir, "costo_rutas.csv")
costos_rutas.to_csv(costo_rutas_csv_path, header=False, index=False)

########################################################################
# Ejecución de escenarios

# Llaves:
#	- rand_seed (1)
#		- perfil (2)
#			- interés (11) [0,1,2,3,4,5,6,7,8,9,10]
#				- buzón (4)

# Values:
#	- costo total
#	- costo financiero sin interés

# abrir archivo
with open(exp_id,'r',encoding='utf-8') as f:
	exp_dict = json.load(f)

# mientras N < N_min
while len(exp_dict) < N_min:
	# agregar una corrida
	exp_dict = agregar_resultado(exp_dict, collections_profiles, std_profiles, n_thr, solver, data_dir=data_dir)
	# guardar dict
	with open(exp_id,'w',encoding='utf-8') as f:
		json.dump(exp_dict,f,indent=2)


# calcular delta_std 
delta_std = calcula_delta_std(exp_dict)
print(f"{delta_std = }")

# mientras delta_std > 0.01 y N < N_max
while delta_std > 0.01 and len(exp_dict) < N_max:
	# agregar una corrida
	exp_dict = agregar_resultado(exp_dict, collections_profiles, std_profiles, n_thr, solver, data_dir=data_dir)
	# guardar dict
	with open(exp_id,'w',encoding='utf-8') as f:
		json.dump(exp_dict,f,indent=2)
	# calcular delta_std
	delta_std = calcula_delta_std(exp_dict)
	print(f"{delta_std = }")

sys.exit()

# print tablita con mean +- std

