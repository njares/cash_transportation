#!/usr/bin/env python3
"""
Genera gráficos comparativos de ganancias a partir de tablas CSV.
"""
import argparse
import os
import sys
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


def plot_ganancias(profile, tabla_df, output_file=None):
    """
    Lee un DataFrame y genera un gráfico de ganancias.
    
    Args:
        profile: nombre del perfil
        tabla_df: DataFrame listo
        output_file: Ruta donde guardar la imagen (opcional)
    """

    plot_df = pd.DataFrame()
    plot_df["interes"] = tabla_df[tabla_df["buzon"] == "0"]["interes"].astype(float).reset_index(drop=True)
    #plot_df.columns = ["interes"]
    for b_idx in range(5):
        plot_df["mean_"+str(b_idx)] = tabla_df[tabla_df["buzon"] == str(b_idx)]["ganancia_mean"].astype(float).reset_index(drop=True)
        plot_df["std_"+str(b_idx)] = tabla_df[tabla_df["buzon"] == str(b_idx)]["ganancia_std"].astype(float).reset_index(drop=True)
    
    # Define the columns to plot and their corresponding error columns
    value_cols = ['mean_0', 'mean_1', 'mean_2', 'mean_3', 'mean_4']
    error_cols = ['std_0', 'std_1', 'std_2', 'std_3', 'std_4']
    labels = ['Capacity 1', 'Capacity 3/4', 'Capacity 1/2', 'Capacity 1/3', 'Capacity 1/4']

    for i, col in enumerate(value_cols):
        plt.errorbar(
            df_final['interes'],
            df_final[col],
            yerr=df_final[error_cols[i]],
            fmt='-o', # Format: line with circles
            label=labels[i], # Label for legend
            capsize=4 # Size of the error bar caps
        )
    
    plt.xlabel('I')
    plt.ylabel('Percentage')
    plt.title(f'Gain with a profile: {profile}')
    plt.legend()
    plt.grid(True)
    
    # Guardar si se especificó un archivo de salida
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"Gráfico guardado en: {output_file}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Genera gráficos comparativos de ganancias a partir de archivos CSV."
    )
    parser.add_argument(
        "--csv-file",
        type=str,
        required=True,
        help="Archivo CSV con los datos de ganancia"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Archivo de salida para guardar la imagen (opcional)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio donde guardar archivos (por defecto: artifacts/reports/)"
    )
    
    args = parser.parse_args()
    
    try:
        # Determinar directorio de salida
        if args.output_dir:
            output_dir = args.output_dir
        else:
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(repo_root, 'artifacts', 'reports')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Determinar ruta de salida
        if args.output:
            output_path = args.output
        else:
            # Generar nombre de archivo basado en el CSV
            base_name = os.path.splitext(os.path.basename(args.csv_file))[0]
            output_path = os.path.join(output_dir, f"ganancias_{base_name}.png")
        
        # parse txt file
        # profiles, tablas_df = parse_txt(args.csv_file)
        
        # # Generar los gráficos
        # for profile, tabla_df in zip(profiles, tablas_df):
        #     #plot_ganancias(profile, tabla_df, output_path)
        #     plot_ganancias(profile, tabla_df, "")
        tabla_df = pd.read_csv(args.csv_file)
        plot_ganancias("constante", tabla_df)

    except Exception as e:
        print(f"Error procesando archivo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

def parse_txt(csv_file):
    with open(csv_file, "r") as file:
        lines = file.readlines()
    profiles = []
    tablas_df = []
    # Tabla constante
    profiles.append(lines[0][:-1])
    tabla = pd.DataFrame([l[:-1].split(",") for l in lines[2:52]])
    tabla.columns = lines[1][:-1].split(",")
    tablas_df.append(tabla)
    # Tabla V
    profiles.append(lines[52][:-1])
    tabla = pd.DataFrame([l[:-1].split(",") for l in lines[54:]])
    tabla.columns = lines[53][:-1].split(",")
    tablas_df.append(tabla)
    return profiles, tablas_df


if __name__ == "__main__":
    main()
