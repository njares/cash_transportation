## Solver en Python-PuLP

Utiliza una versión precompilada de CBC, según lo que dice la documentación.

Para poder utilizarlo con el ejemplo de las 3 rutas en enero, en primera medida se puede desde ipython (más sencillo):

* run model.py

* problem = model_problem(amount_of_branches=3, amount_of_days=31, amount_of_routes=5, box_amounts_csv="data/buzon.csv", business_days_csv="data/habiles.csv", cash_in_branch_csv="data/e0.csv", collection_csv="data/recaudacion.csv", cost_routes_csv="data/costo_rutas.csv", route_branches_csv="data/rutas.csv")

* Se puede agregar debug=True para imprimir todas las variables generadas y medir la cantidad de tiempo que le toma al solver encontrar la solución (default en False)

* Se puede agregar last_days_collection para decirle que recolecte dinero en un conjunto de das (default en [])

* Se puede agregar extra_box_percent=P donde P es el porcentaje (1.0 = 100%) que se quiere permitir extra en los buzones (default en 0.0).

El objeto 'problem' es el problema ya resuelto como objeto de PuLP.

Se puede obtener el costo total del schedule con el comando:

    pulp.value(problem.objective)

Se puede obtener los dias en los que se usa cada ruta con:

    for var in problem.variables()
        if var.varValue == 1:
            print(var.name, " = ", var.varValue)
