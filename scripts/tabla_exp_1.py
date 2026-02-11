#!/usr/bin/env python3
"""
Genera tablas resumen de experimentos con estadísticas (mean y std) para diferentes costos y ganancias.
"""
import json
import numpy as np
import argparse
import os
import sys


def ver_tabla(tabla, std_output=False, csv_file=None):
    """Imprime una tabla formateada."""
    
    def _print(s):
        if std_output:
            print(s)
        if csv_file:
            csv_file.write(s)
            csv_file.write('\n')
    
    # Imprimir encabezado
    headers = [
        "buzon", "interes", 
        "costo_logistico_mean", "costo_logistico_std",
        "costo_financiero_mean", "costo_financiero_std",
        "costo_total_mean", "costo_total_std",
        "costo_logistico_financiero_mean", "costo_logistico_financiero_std",
        "costo_financiero_financiero_mean", "costo_financiero_financiero_std",
        "costo_total_financiero_mean", "costo_total_financiero_std",
        "ganancia_mean", "ganancia_std"
    ]
    
    _print(','.join(headers))
    
    for row in tabla:
        _print(ver_fila(row))


def ver_fila(fila):
    """Devuelve una fila formateada."""
    
    # Formatear cada par de valores (mean, std) como dos columnas separadas por coma
    values = []
    
    # Añadir buzon y interes (primera fila de cada grupo)
    buzon = int(fila[0])  # buzon está en la posición 0
    interes = fila[1]     # interes está en la posición 1
    values.append(str(buzon))
    values.append(f"{interes:.1f}")
    
    # Añadir las 14 estadísticas (7 pares de mean/std)
    for i in range(2, 14, 2):  # desde posición 2 hasta 14, de 2 en 2
        mean_val = 1e3 * fila[i]
        std_val = 1e3 * fila[i+1]
        values.append(f"{mean_val:.2G}")
        values.append(f"{std_val:.2G}")
    
    # Añadir la ganancia como porcentaje (últimas 2 columnas)
    ganancia_mean = 100 * fila[14]
    ganancia_std = 100 * fila[15]
    values.append(f"{ganancia_mean:.2G}")
    values.append(f"{ganancia_std:.2G}")
    
    return ','.join(values)


def parse_experiment(exp_id):
    """
    Parsea el archivo de experimento y retorna el diccionario.
    Si exp_id es solo un nombre, busca en experiments/runs/.
    """
    # Si es solo un nombre, buscar en experiments/runs
    if os.path.sep not in exp_id and not exp_id.startswith('/'):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        exp_id = os.path.join(repo_root, 'experiments', 'runs', exp_id)
    
    if not os.path.exists(exp_id):
        raise FileNotFoundError(f"Archivo de experimento no encontrado: {exp_id}")
    
    with open(exp_id, 'r', encoding='utf-8') as f:
        exp_dict = json.load(f)
    
    return exp_dict


def generate_tables(exp_dict, std_output=False, csv_file=None):
    """
    Genera las tablas de resumen para cada perfil.
    
    Estructura esperada del exp_dict:
    - Llaves: rand_seed (string) -> interés -> buzón -> [costo_total, costo_financiero_sin_interes]
    - Excluye '_meta' del conteo de seeds
    
    Args:
        exp_dict: Diccionario con los resultados del experimento
        std_output: (opcional): Imprime la tabla en stdout. Por defecto no imprime a stdout.
        csv_file: (opcional): Archivo de texto donde escribir la tabla. Por defecto no se escribe la tabla.
    """
    
    # Get actual seed keys, excluding _meta
    seed_keys = [k for k in exp_dict.keys() if k != '_meta']
    N_exp = len(seed_keys)
    
    if N_exp == 0:
        print("Error: No se encontraron seeds en el experimento (posiblemente vacío)")
        return
    
    # 50 filas (5 buzones × 10 intereses)
    # 16 columnas (buzon, interes, 7 estadísticas con 2 columnas cada una)
    # Tabla vacía
    tabla = np.zeros((50, 16))
    # Tamaños de buzones nuevos: [1, 3/4, 1/2, 1/3, 1/4]
    buzones_sizes = [1, 3/4, 1/2, 1/3, 1/4]
    for buzon_idx, buzon_size in enumerate(buzones_sizes):
        for interes_anual in np.linspace(1, 10, 10):
            cur_fila = int(buzon_idx*10 + (interes_anual-1))
            interes = (1+interes_anual/100)**(1/365)-1
            
            # caso logístico
            # costo logístico
            costos_logisticos_logistico = []
            for seed in seed_keys:
                try:
                    if len(exp_dict[seed]['0.0'][str(buzon_idx)]) == 2:
                        costos_logisticos_logistico.append(exp_dict[seed]['0.0'][str(buzon_idx)][0])
                    else:
                        print(exp_dict[seed]['0.0'][str(buzon_idx)][2])
                except (KeyError, IndexError):
                    continue
            
            if len(costos_logisticos_logistico) == 0:
                continue
            
            mean = np.mean(costos_logisticos_logistico)
            std = np.std(costos_logisticos_logistico)
            tabla[cur_fila, 0] = buzon_idx  # buzon
            tabla[cur_fila, 1] = interes_anual  # interes
            tabla[cur_fila, 2] = mean
            tabla[cur_fila, 3] = std
            
            # costo financiero
            costos_financieros_logistico = []
            for seed in seed_keys:
                try:
                    if len(exp_dict[seed]['0.0'][str(buzon_idx)]) == 2:
                        costos_financieros_logistico.append(exp_dict[seed]['0.0'][str(buzon_idx)][1]*interes)
                    else:
                        print(exp_dict[seed]['0.0'][str(buzon_idx)][2])
                except (KeyError, IndexError):
                    continue
            
            mean = np.mean(costos_financieros_logistico)
            std = np.std(costos_financieros_logistico)
            tabla[cur_fila, 4] = mean
            tabla[cur_fila, 5] = std
            
            # costo total
            costos_total_logistico = [c_log + c_fin for c_log, c_fin in zip(costos_logisticos_logistico, costos_financieros_logistico)]
            mean = np.mean(costos_total_logistico)
            std = np.std(costos_total_logistico)
            tabla[cur_fila, 6] = mean
            tabla[cur_fila, 7] = std
            
            # caso financiero
            # costo financiero
            costos_financieros_financiero = []
            for seed in seed_keys:
                try:
                    if len(exp_dict[seed]['0.0'][str(buzon_idx)]) == 2:
                        costos_financieros_financiero.append(exp_dict[seed][str(interes_anual)][str(buzon_idx)][1]*interes)
                    else:
                        print(exp_dict[seed]['0.0'][str(buzon_idx)][2])
                except (KeyError, IndexError):
                    continue
            
            mean = np.mean(costos_financieros_financiero)
            std = np.std(costos_financieros_financiero)
            tabla[cur_fila, 10] = mean
            tabla[cur_fila, 11] = std
            
            # costo total
            costos_total_financiero = []
            for seed in seed_keys:
                try:
                    if len(exp_dict[seed]['0.0'][str(buzon_idx)]) == 2:
                        costos_total_financiero.append(exp_dict[seed][str(interes_anual)][str(buzon_idx)][0])
                    else:
                        print(exp_dict[seed]['0.0'][str(buzon_idx)][2])
                except (KeyError, IndexError):
                    continue
            
            mean = np.mean(costos_total_financiero)
            std = np.std(costos_total_financiero)
            tabla[cur_fila, 12] = mean
            tabla[cur_fila, 13] = std
            
            # costo logístico
            costos_logistico_financiero = [c_tot - c_fin for c_tot, c_fin in zip(costos_total_financiero, costos_financieros_financiero)]
            mean = np.mean(costos_logistico_financiero)
            std = np.std(costos_logistico_financiero)
            tabla[cur_fila, 8] = mean
            tabla[cur_fila, 9] = std
            
            # ganancia
            ganancias = [(c_log - c_fin) / c_log for c_log, c_fin in zip(costos_total_logistico, costos_total_financiero)]
            mean = np.mean(ganancias)
            std = np.std(ganancias)
            tabla[cur_fila, 14] = mean
            tabla[cur_fila, 15] = std
    
    if csv_file:
        with open(csv_file, 'w', encoding='utf-8') as f:
            ver_tabla(tabla, std_output, f)
    else:
        ver_tabla(tabla, std_output, csv_file)


def main():
    parser = argparse.ArgumentParser(
        description="Genera tablas resumen de experimentos con estadísticas (mean ± std)"
    )
    parser.add_argument(
        "--exp-id",
        type=str,
        default="exp_test.json",
        help="Archivo JSON del experimento (si es nombre simple, se busca en experiments/runs/)"
    )
    parser.add_argument(
        "--std-output", 
        action="store_true", 
        help="Si se incluye, imprime la salida en la terminal"
    )
    parser.add_argument(
        "--csv-output",
        type=str,
        nargs='?',
        const='',
        default=None,
        help="Archivo de texto donde escribir la tabla. Si no se especifica ruta, se genera automáticamente en artifacts/reports/tabla_<exp-id>.csv. Si se especifica ruta, usa esa ruta"
    )
    args = parser.parse_args()
    
    try:
        exp_dict = parse_experiment(args.exp_id)
        
        # Determine output path
        csv_file = args.csv_output
        
        if csv_file == "":
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(repo_root, 'artifacts', 'reports')
            os.makedirs(output_dir, exist_ok=True)
            # Generate base filename from exp_id if not specified
            base_name = os.path.splitext(os.path.basename(args.exp_id))[0]
            csv_file = os.path.join(output_dir, f"tabla_{base_name}.csv")
        
        generate_tables(exp_dict, args.std_output, csv_file)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error procesando experimento: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
