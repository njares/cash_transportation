import os

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
    l_d_c = [i for i in range(l_d_c.size) if l_d_c[i]==1]

    return n_d, n_p, n_s, big_M, nombres, costs/rutas.sum(1) , e_zero, l_d_c, nombres_rutas
