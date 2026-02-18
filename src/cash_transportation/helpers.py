import os
import sys
import time
import itertools
from scipy.special import comb
import numpy as np
import pandas as pd

# Use the packaged solverpulp model from the new location
from cash_transportation.solvers.solverpulp import model


def calculo_recaudaciones(prop_suc, collections, e_zero, buzones):
    # ToDo: propagar prop_suc
    return collections, e_zero, buzones


def calculo_ganancia(business_days, rutas, costos_rutas, interes, prop_suc, collections, e_zero, buzones, n_thr=4, solver='cbc', debug=False, data_dir: str = './data/generated/'):
    os.makedirs(data_dir, exist_ok=True)

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

    _, n_d = business_days.shape
    n_p, n_s = rutas.shape

    # Calcular con costo financiero
    status, variables, Problems = model.model_problem(
        n_d, n_s, n_p,
        rutas_csv_path, costo_rutas_csv_path, e_zero_csv_path,
        buzones_csv_path, habiles_csv_path, recaudacion_csv_path,
        daily_interest_rate=interes, n_thr=n_thr, solver=solver, debug=debug
    )
    try:
        costos_total_caso_financiero = sum([prob.objective.value() for prob in Problems])
    except Exception:
        return -1

    # Calcular sin costo financiero
    status, variables, Problems = model.model_problem(
        n_d, n_s, n_p,
        rutas_csv_path, costo_rutas_csv_path, e_zero_csv_path,
        buzones_csv_path, habiles_csv_path, recaudacion_csv_path,
        daily_interest_rate=0.0, n_thr=n_thr, solver=solver, debug=debug
    )
    try:
        costos_logístico_sin_financiero = sum([prob.objective.value() for prob in Problems])
    except Exception:
        return -1

    # Calcular costo financiero del caso logístico
    costos_financiero_logístico = e_zero.values.sum()
    for var in variables:
        var_id = var.name.split('_')[0]
        if var_id == 'e':
            suc, dia = var.name.split('_')[1:]
            if dia != n_d-1:
                costos_financiero_logístico += var.varValue
    costos_financiero_logístico *= interes

    costos_total_caso_logistico = costos_financiero_logístico + costos_logístico_sin_financiero

    ganancia = (costos_total_caso_logistico - costos_total_caso_financiero) / costos_total_caso_logistico

    return ganancia


def generar_escenarios(n_s, n_p, n):
    cant_rutas_posibles = 2**n_s - n_s - 1
    cant_rutas_elegir = n_p - n_s
    # Generar la lista de números que determinan cada ruta no trivial
    rutas_posibles = list(range(2**n_s))
    rutas_posibles.remove(0)
    for i in range(n_s):
        rutas_posibles.remove(2**i)
    # Generar listas de tamaño n_p-n_s de índices de esa lista
    escenarios_posibles = itertools.combinations(range(cant_rutas_posibles), cant_rutas_elegir)
    # Elegir n de esas listas
    N = int(comb(cant_rutas_posibles, cant_rutas_elegir))
    indices_escenarios = np.random.choice(N, n, replace=False)
    r = iter(range(N))
    # filter
    indices_rutas = [next(escenarios_posibles) for _ in range(N) if next(r) in indices_escenarios]
    # Generar las rutas
    escenarios = []
    fmt_str = "{:0"+str(n_s)+"b}"
    for indices in indices_rutas:
        rutas = [rutas_posibles[i] for i in indices]
        rutas = [fmt_str.format(ruta) for ruta in rutas]
        rutas = [list(map(int, ruta)) for ruta in rutas]
        rutas = np.vstack([np.eye(n_s), rutas])
        rutas = pd.DataFrame(rutas)
        escenarios.append(rutas)
    return escenarios


def agregar_resultado(exp_dict, collection_profile, std, profile_name, n_thr, solver, debug=False, data_dir: str = './data/generated/'):
    os.makedirs(data_dir, exist_ok=True)
    rutas_csv_path = os.path.join(data_dir, "rutas.csv")
    costo_rutas_csv_path = os.path.join(data_dir, "costo_rutas.csv")
    habiles_csv_path = os.path.join(data_dir, "habiles.csv")
    buzones_sizes = [1, 3/4, 1/2, 1/3, 1/4]
    # ensure meta container for cumulative timing
    if '_meta' not in exp_dict:
        exp_dict['_meta'] = {"total_runtime_seconds": 0.0}
    # generar semilla
    rand_seed = len(exp_dict)-1
    exp_dict[str(rand_seed)] = {}
    seed_runtime = 0.0
    # generar perfil aleatorio
    rng = np.random.default_rng(seed=rand_seed)
    n_s, n_d = collection_profile.shape
    #n_p,_ = rutas.shape
    n_p = 8
    e_zero = collection_profile[:, 0]
    mu = e_zero[0]
    if std == 0:
        rand_collect = np.zeros(collection_profile.shape)
        rand_e_zero = np.zeros(e_zero.shape)
    else:
        alpha = 1/(std**2)
        theta = mu/alpha
        rand_collect = rng.gamma(alpha, theta, size=collection_profile.shape) - mu
        rand_e_zero = rng.gamma(alpha, theta, size=e_zero.shape) - mu
    collections = collection_profile + rand_collect
    e_zero = e_zero + rand_e_zero
    collections = pd.DataFrame(collections)
    e_zero = pd.DataFrame(e_zero)
    # guardar perfil aleatorio
    # Recaudaciones por sucursal
    recaudacion_csv_path = os.path.join(data_dir, "recaudacion.csv")
    # Recaudacion inicial
    e_zero_csv_path = os.path.join(data_dir, "e0.csv")
    for interes_anual in np.linspace(0, 10, 11):
        interes = (1+interes_anual/100)**(1/365)-1
        exp_dict[str(rand_seed)][str(interes_anual)] = {}
        #cantidad de recolecciones mensuales
        for b in range(5):
            buzones = np.ones(n_s)*buzones_sizes[b]
            collections_clip = collections.clip(lower=0.0, upper=buzones_sizes[b])
            e_zero_clip = e_zero.clip(lower=0.0, upper=buzones_sizes[b])
            collections_clip.to_csv(recaudacion_csv_path, header=False, index=False, sep="\t")
            e_zero_clip.to_csv(e_zero_csv_path, header=False, index=False)
            buzones = pd.DataFrame(buzones)
            # Datos de buzones
            buzones_csv_path = os.path.join(data_dir, "buzon.csv")
            buzones.to_csv(buzones_csv_path, header=False, index=False)
            print(f"Resolviendo caso {rand_seed} {interes_anual} {b} ", end="")
            start = time.time()
            # Resolver problema
            status, variables, Problems = model.model_problem(
                n_d, n_s, n_p,
                rutas_csv_path, costo_rutas_csv_path, e_zero_csv_path,
                buzones_csv_path, habiles_csv_path, recaudacion_csv_path,
                daily_interest_rate=interes, n_thr=n_thr, solver=solver, debug=debug
            )
            tiempo = time.time()-start
            print(f"t={tiempo:.2f}")
            seed_runtime += tiempo
            if status[0] != 'Resuelto (Óptimo)':
                exp_dict[str(rand_seed)][str(interes_anual)][str(b)] = [None, None, status[0]]
                continue
            else:
                try:
                    if solver == "gurobi":
                        import gurobipy as gp
                        problem = Problems[0]
                        gurobi_model = problem.solverModel
                        num_solutions = gurobi_model.SolCount
                        if num_solutions > 1:
                            # print(f"Number of solutions found: {num_solutions}")
                            gurobi_model.setParam(gp.GRB.Param.SolutionNumber, rand_seed % num_solutions)
                            variables = []
                            variables += problem.variables()
                    # Calcular costo total
                    costo_total = sum([prob.objective.value() for prob in Problems])
                    # Calcular costo financiero sin interés
                    costo_financiero = e_zero.values.sum()
                    for var in variables:
                        var_id = var.name.split('_')[0]
                        if var_id == 'e':
                            _, dia = var.name.split('_')[1:]
                            if int(dia) != n_d-1:
                                costo_financiero += var.solverVar.Xn
                    exp_dict[str(rand_seed)][str(interes_anual)][str(b)] = [costo_total, costo_financiero]
                    # es sin interés, porque para el costo financiero real
                    # se necesita la siguiente linea:
                    # costos_financiero_logístico *= interes
                except Exception as e:
                    exp_dict[str(rand_seed)][str(interes_anual)][str(b)] = [None, None, f"Error: {str(e)}"]
                    continue
    # store per-seed runtime and update global meta
    exp_dict[str(rand_seed)]['_runtime_seconds'] = seed_runtime
    try:
        exp_dict['_meta']['total_runtime_seconds'] += seed_runtime
    except Exception:
        # if meta was somehow corrupted, reset it safely
        exp_dict['_meta'] = {"total_runtime_seconds": seed_runtime}
    return exp_dict


def calcula_delta_std(exp_dict):
    # Get actual seed keys, excluding _meta
    seed_keys = [k for k in exp_dict.keys() if k != '_meta']
    N_seeds = len(seed_keys)
    delta_std = 0.0  # quiero la máxima delta_std
    # para cada exp_setup
    for interes_anual in np.linspace(0, 10, 11):
        for b in range(5):
            # recorrer las seeds
            costos_totales = []
            costos_financi = []
            for seed_key in seed_keys:
                try:
                    costo_total = exp_dict[seed_key][str(interes_anual)][str(b)][0]
                    costo_financiero = exp_dict[seed_key][str(interes_anual)][str(b)][1]
                    
                    # Verificar que los valores no sean None o inválidos
                    if costo_total is not None and costo_financiero is not None:
                        costos_totales.append(costo_total)
                        costos_financi.append(costo_financiero)
                except (KeyError, IndexError, TypeError):
                    # Skip si hay estructura incompleta o valores inválidos
                    continue
            # Need at least 2 data points to calculate delta_std
            if len(costos_totales) < 3:
                continue
            # calcular las std
            std_total_last = np.std(costos_totales)
            std_finan_last = np.std(costos_financi)
            std_total_prev = np.std(costos_totales[:-1])
            std_finan_prev = np.std(costos_financi[:-1])
            # ver la variación porcentual
            if std_total_last == 0 or std_total_prev == 0:
                delta_std_total = 0.0
            else:
                delta_std_total = np.abs((std_total_last-std_total_prev)/std_total_last)
            if std_finan_last == 0 or std_finan_prev == 0:
                delta_std_finan = 0.0
            else:
                delta_std_finan = np.abs((std_finan_last-std_finan_prev)/std_finan_last)
            current_delta_std = max(delta_std_total, delta_std_finan)
            delta_std = max(current_delta_std, delta_std)
    return delta_std

# From previous main/helpers.py: Excel-to-CSV generator
def generate_csvs(excel_df, sheet_name, data_dir="./data"):
    """
    Función para generar archivos CSV que alimentan el modelo de PuLP.
    """
    dataframe = excel_df.get(sheet_name, None)
    if dataframe is None:
        raise Exception("No hay hoja {}.".format(sheet_name))

    # Obtener datos del modelo generales
    datos_modelo = dataframe.iloc[26]
    datos_modelo_csv_path = os.path.join(data_dir, "datos_modelo.csv")
    datos_modelo_csv = open(datos_modelo_csv_path, "w")
    datos_modelo_csv.write(
        "{}, {}, {}, {}".format(
            datos_modelo[0],
            datos_modelo[1],
            datos_modelo[2],
            datos_modelo[3],
        )
    )
    datos_modelo_csv.close()

    # Variables principales para ubicarnos en el DF
    n_d = datos_modelo[0]
    n_p = datos_modelo[1]
    n_s = datos_modelo[2]
    big_M = datos_modelo[3]

    # Nombres sucursales
    nombres = dataframe.iloc[1, 1: 1 + n_s]

    # Nombres rutas
    nombres_rutas = dataframe.iloc[2: 2 + n_p, 0]
    # Datos de rutas
    rutas = dataframe.iloc[2: 2 + n_p, 1: 1 + n_s]
    rutas_csv_path = os.path.join(data_dir, "rutas.csv")
    rutas.to_csv(rutas_csv_path, header=False, index=False)

    # Datos de buzones
    buzones = dataframe.iloc[28: 28 + n_s, 1]
    buzones_csv_path = os.path.join(data_dir, "buzon.csv")
    buzones.to_csv(buzones_csv_path, header=False, index=False)

    # Recaudacion inicial
    e_zero = dataframe.iloc[28: 28 + n_s, 2]
    e_zero_csv_path = os.path.join(data_dir, "e0.csv")
    e_zero.to_csv(e_zero_csv_path, header=False, index=False)

    # Costos por ruta
    costs = dataframe.iloc[2: 2 + n_p, 9]
    costo_rutas_csv_path = os.path.join(data_dir, "costo_rutas.csv")
    costs.to_csv(costo_rutas_csv_path, header=False, index=False)

    # Dias habiles por ruta
    business_days = dataframe.iloc[2: 2 + n_p, 19: 19 + n_d]
    habiles_csv_path = os.path.join(data_dir, "habiles.csv")
    business_days.to_csv(habiles_csv_path, header=False, index=False)

    # Recaudaciones por sucursal
    collections = dataframe.iloc[28: 28 + n_s, 3: 3 + n_d]
    recaudacion_csv_path = os.path.join(data_dir, "recaudacion.csv")
    collections.to_csv(recaudacion_csv_path, header=False, index=False, sep="\t")

    # Días obligatorios
    l_d_c = dataframe.iloc[23, 19: 19 + n_d]
    l_d_c = l_d_c.to_numpy().flatten()
    l_d_c = [i for i in range(l_d_c.size) if l_d_c[i] == 1]

    return n_d, n_p, n_s, big_M, nombres, costs/rutas.sum(1), e_zero, l_d_c, nombres_rutas
