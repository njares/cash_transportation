import numpy as np
import pandas as pd
import pulp
import time

BIG_M = 30000000
TN_DAILY_INTEREST_RATE = 0.00092

def model_problem(
    amount_of_days, amount_of_branches, amount_of_routes,
    route_branches_csv, cost_routes_csv, cash_in_branch_csv,
    box_amounts_csv, business_days_csv, collection_csv,
    last_days_collection=list(), extra_box_percent=0.0, daily_interest_rate=0.0,
    debug=False, solver='cbc', n_thr=4):
    """
    Función que modela y resuelve el problema de envío de camiones de acuerdo a los datos
    de entrada, que vienen en forma de CSVs.
    - amount_of_days: Cantidad de días de planeamiento.
    - amount_of_branches: Cantidad de sucursales en la planificación.
    - amount_of_routes: Cantidad de rutas diferentes comprendidas en la planificación.
    - *_csv: CSVs con los datos que deben incorporarse, ejemplos en carpeta 'data/'
    - last_days_collection: Lista de los días en los que se debe ir a buscar dinero. Suelen ser los últimos n
    - extra_box_percent: Porcentaje extra que se permite guardar de dinero en cada sucursal.
    - daily_interest_rate: Tasa diaria de interés, para incorporar costo financiero.
    - debug: Permite imprimir todas las variables del problema, default False.
    - scip: True si se utilizará SCIP para resolver, False si se usará CBC.
    """
    
    if daily_interest_rate < 0.0:
        print("ERROR: Tasa de interes no puede ser menor a cero (al menos en Argentina...)")
        return None, [], []
    
    # Validar datos de entrada
    try:
        routes_matrix = np.loadtxt(route_branches_csv, delimiter=",")
        separable = (routes_matrix.size == 1) or np.array_equal(routes_matrix, np.diag(np.diag(routes_matrix)))
    except Exception as e:
        print(f"ERROR: No se pudo cargar la matriz de rutas desde {route_branches_csv}: {str(e)}")
        return None, [], []
    
    problems = range(amount_of_branches) if separable else [0]
    days = range(amount_of_days)
    branches = range(amount_of_branches)
    routes = range(amount_of_routes)
    
    #### DATOS
    try:
        # Sucursales en cada ruta        
        route_branches_df = pd.read_csv(route_branches_csv, header=None)
        route_branches = {
            ridx: list(route_branches_df.iloc[ridx]) for ridx in routes
        }
        if debug:
            print("route_branches = {}".format(route_branches))
        
        # Costo de tomar cada ruta
        cost_routes_df = pd.read_csv(cost_routes_csv, header=None)
        cost_routes = {
            ridx: float(cost_routes_df.iloc[ridx,0]) for ridx in routes
        }
        if debug:
            print("cost_routes = {}".format(cost_routes))
        
        # Efectivo inicial en cada sucursal
        cash_branches_df = pd.read_csv(cash_in_branch_csv, header=None)
        first_cash_in_branch = [
            float(cash_branches_df.iloc[bidx,0]) for bidx in branches
        ]
        if debug:
            print("first_cash_in_branch = {}".format(first_cash_in_branch))
        
        # Efectivo máximo de cada buzón
        box_amounts_df = pd.read_csv(box_amounts_csv, header=None)
        box_max = [
            float(box_amounts_df.iloc[bidx,0]) for bidx in branches
        ]
        if debug:
            print("box_max = {}".format(box_max))
        
        # Días hábiles por ruta
        business_days_df = pd.read_csv(business_days_csv, header=None)
        business_days = {
            ridx: list(business_days_df.iloc[ridx]) for ridx in routes
        }
        if debug:
            print("business_days = {}".format(business_days))
        
        # Recaudacion por sucursal por dia
        collection_df = pd.read_csv(collection_csv, header=None, sep="\t")
        collection = {
            bidx: list(collection_df.iloc[bidx]) for bidx in branches
        }
        if debug:
            print("collection = {}".format(collection))

    except Exception as e:
        print(f"ERROR: No se pudieron cargar los datos desde los archivos CSV: {str(e)}")
        return None, [], []
    
    msg_flag = False
    if debug:
        start = time.time()
        msg_flag = True
    
    status = []
    variables = []
    Problems = []

    for prob in problems:
        try:
            problem = pulp.LpProblem("MinimizeCosts", pulp.LpMinimize)
            
            #### INCOGNITAS
            if separable:
                branches = [prob]
                routes = [prob]
            
            # Variables X: retira o no por día y por ruta.
            days_routes = {
                ridx: {
                    didx: pulp.LpVariable(
                        "x_{}_{}".format(str(didx), str(ridx)),
                        cat=pulp.LpBinary,
                    ) for didx in days
                } for ridx in routes
            }
            if debug:
                print("days_routes = {}".format(days_routes))
            
            # Variables E: efectivo por sucursal y por día
            # lowBound=0 --->  0 <= e[s,d]
            branch_cash = {
                bidx: {didx: pulp.LpVariable(
                        "e_{}_{}".format(str(bidx), str(didx)),
                        lowBound=0,
                        cat=pulp.LpContinuous,
                    ) for didx in days
                } for bidx in branches
            }
            if debug:
                print("branch_cash = {}".format(branch_cash))
            
            # Variables T: efectivo retirado por sucursal por dia por ruta
            # lowBound=0 ---> 0 <= t[s,d,p]
            withdrawn_cash = {
                bidx: {
                    didx: {
                        ridx: pulp.LpVariable(
                            "t_{}_{}_{}".format(bidx, didx, ridx),
                            lowBound=0,
                            cat=pulp.LpContinuous,
                        ) for ridx in routes
                     } for didx in days
                } for bidx in branches
            }
            if debug:
                print("withdrawn_cash = {}".format(withdrawn_cash))
            
            #### FUNCION OBJETIVO
            cost_function = None
            for index in days_routes.keys():
                cost_function += sum(days_routes[index].values()) * cost_routes[index]
            
            if daily_interest_rate > 0.0:
                cost_function += sum([first_cash_in_branch[bidx] * daily_interest_rate for bidx in branches])
                cost_function += sum([branch_cash[bidx][day] * daily_interest_rate for bidx in branches for day in days[:-1]])
            
            problem += cost_function
            
            #### RESTRICCIONES

            # e[s,1] == e0[s,1] + r[s,1] - sum <p> in P: (t[s,1,p])
            # e[s,d] == e[s,d-1] + r[s,d] - sum <p> in P: (t[s,d,p])
            for bidx in branches:
                problem += branch_cash[bidx][0] == first_cash_in_branch[bidx] + collection[bidx][0] - sum([withdrawn_cash[bidx][0][route] for route in routes])
                for day in days[1:]:
                    problem += (
                        branch_cash[bidx][day]
                        == 
                        branch_cash[bidx][day - 1] + collection[bidx][day] - sum([withdrawn_cash[bidx][day][route] for route in routes])
                    )
            
            # forall <d,p> in D*P:
            #     sum <s> in S: (m[s,p]*t[s,d,p]) <= M * x[d,p];
            for day in days:
                for route in routes:
                    problem += sum([route_branches[route][bidx] * withdrawn_cash[bidx][day][route] for bidx in branches]) <= BIG_M * days_routes[route][day]
            
            # forall <d,p> in D*P:
            #     sum <s> in S: ((1-m[s,p])*t[s,d,p]) == 0;
            for day in days:
                for route in routes:
                    problem += sum([(1 - route_branches[route][bidx]) * withdrawn_cash[bidx][day][route] for bidx in branches]) == 0
            
            # forall <s,d> in S*D:
            #     e[s,d] <= b[s]*1.17;
            for day in days:
                for bidx in branches:
                    problem += branch_cash[bidx][day] <= box_max[bidx] * (1.0 + extra_box_percent)
            
            # forall <s,d,p> in S*(D-{1})*P:
            #    t[s,d,p] <= e[s,d-1];
            for branch in branches:
                problem += sum([withdrawn_cash[branch][0][route] for route in routes]) <= first_cash_in_branch[branch]
                for day in days[1:]:
                    problem += sum([withdrawn_cash[branch][day][route] for route in routes]) <= branch_cash[branch][day - 1]
            
            # forall <d,p> in D*P:
            #     x[d,p] <= h[d,p];
            for day in days:
                for route in routes:
                    problem += days_routes[route][day] <= business_days[route][day]
            
            # recollection on D_q days
            if len(last_days_collection) > 0:
                for bidx in branches:
                    problem += sum([
                        route_branches[route][bidx] * days_routes[route][day]
                        for route in routes for day in last_days_collection
                    ]) >= 1
            
            solv = None
            
            if solver=='scip':
                 solv = pulp.apis.SCIP_CMD(msg=msg_flag)
            elif solver == 'fscip':
                solv = pulp.apis.FSCIP_CMD(msg=msg_flag)
            elif solver == 'cbc':
                solv = pulp.PULP_CBC_CMD(strong=1, msg=msg_flag, presolve=1, threads=n_thr)
            elif solver == "cuopt":
                solv = pulp.CUOPT(msg=msg_flag)
            elif solver == "gurobi":
                solv = pulp.GUROBI(msg=msg_flag, threads=n_thr)
            elif solver == "HiGHS":
                solv = pulp.HiGHS(msg=msg_flag, threads=n_thr)
            else:
                print("WARNING: Unkown solver, defaulting to cbc")
                solv = pulp.PULP_CBC_CMD(strong=1, msg=msg_flag, presolve=1, threads=n_thr)
            
            try:
                problem.solve(solver=solv)
                
                # Verificar el estado de resolución
                if problem.status == pulp.LpStatusOptimal:
                    cur_status = 'Resuelto (Òptimo)'
                elif problem.status == pulp.LpStatusInfeasible:
                    cur_status = 'No factible'
                elif problem.status == pulp.LpStatusUnbounded:
                    cur_status = 'No acotado'
                elif problem.status == pulp.LpStatusUndefined:
                    cur_status = 'Error no definido (Undefined)'
                elif problem.status == pulp.LpStatusNotSolved:
                    cur_status = 'No resuelto'
                else:
                    cur_status = f'Estado desconocido ({problem.status})'
                
                # Verificar si hay errores en las restricciones
                for bidx in branches:
                    if max(collection[bidx]) > box_max[bidx] * (1.0 + extra_box_percent):
                        cur_status += ', capacidad de buzón superada'
                        break
                
                if len(routes)==1:
                    last_days_business = [d for d in last_days_collection if business_days[routes[0]][d]==1]
                    if len(last_days_collection)>0 and len(last_days_business)==0:
                        cur_status += ', día/s obligatorio/s infactible/s'
                
                status.append(cur_status)
                Problems.append(problem)
                variables += problem.variables()
            
            except Exception as e:
                print(f"ERROR: Fallo al resolver el problema con solver {solver}: {str(e)}")
                status.append('Error de resolución')
                Problems.append(problem)
                variables += problem.variables()
                return status, variables, Problems
        
        except Exception as e:
            print(f"ERROR: Fallo al construir el problema {prob}: {str(e)}")
            return None, [], []
    
    if debug:
        print("Solver took {} seconds.".format(time.time() - start))
    
    return status, variables, Problems
