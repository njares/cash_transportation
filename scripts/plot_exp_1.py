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
import matplotlib as mpl


def plot_ganancias(tabla_df, output_file=None):
    """
    Lee un DataFrame y genera un gráfico de ganancias.
    
    Args:
        tabla_df: DataFrame listo
        output_file: Ruta donde guardar la imagen (opcional)
    """

    plot_df = pd.DataFrame()
    plot_df["interes"] = tabla_df[tabla_df["buzon"] == 0]["interes"].astype(float).reset_index(drop=True)
    #plot_df.columns = ["interes"]
    for b_idx in range(5):
        plot_df["mean_"+str(b_idx)] = tabla_df[tabla_df["buzon"] == b_idx]["ganancia_mean"].astype(float).reset_index(drop=True)
        plot_df["std_"+str(b_idx)] = tabla_df[tabla_df["buzon"] == b_idx]["ganancia_std"].astype(float).reset_index(drop=True)
    
    # Define the columns to plot and their corresponding error columns
    value_cols = ['mean_0', 'mean_1', 'mean_2', 'mean_3', 'mean_4']
    error_cols = ['std_0', 'std_1', 'std_2', 'std_3', 'std_4']
    labels = ['Capacity 1', 'Capacity 3/4', 'Capacity 1/2', 'Capacity 1/3', 'Capacity 1/4']
    fmt_list = ['-o', '-s', '-^', '-d', '-p']
    
    # Configuración matplotlib
    mpl.rcParams['pdf.fonttype'] = 42
    mpl.rcParams['ps.fonttype'] = 42
    plt.rcParams['text.usetex'] = True
    mpl.rcParams['font.family'] = 'Computer Modern'
    
    #fig = plt.figure(figsize=(2.85,2.85),dpi=300) # Tamaño en pulgadas (ancho, alto)
    fig = plt.figure(figsize=(6,6),dpi=300) # Tamaño en pulgadas (ancho, alto)
    ax = plt.axes((0.1,0.1,0.8,0.8)) # Tamaño en (0,1), (left, bottom, width, height)
    
    ax.set_xticks([1,2,3,4,5,6,7,8,9,10])
    ax.set_yticks([0,10,20,30,40,50,60,70])
    
    for i, col in enumerate(value_cols):
        ax.errorbar(
            plot_df['interes'],
            plot_df[col],
            yerr=plot_df[error_cols[i]],
            fmt=fmt_list[i], # Format: line with circles
            label=labels[i], # Label for legend
            capsize=4 # Size of the error bar caps
        )
    
    ax.set_xlabel('Interest ($\mu$)')
    ax.set_ylabel('Mean Gain')
    # plt.title(f'Gain')
    ax.legend()
    # plt.grid(True)
    ax.set_ylim(-5, 75)
    
    # Guardar
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Gráfico guardado en: {output_file}")


def parse_csv(csv_file):
    """
    Parsea el archivo csv y devuelve un dataframe.
    Si csv_file es solo un nombre, busca en artifacts/reports.
    """
    # Si es solo un nombre, buscar en artifacts/reports
    if os.path.sep not in csv_file and not csv_file.startswith('/'):
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_file = os.path.join(repo_root, 'artifacts', 'reports', csv_file)
    
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Archivo csv no encontrado: {csv_file}")
    
    tabla_df = pd.read_csv(csv_file)

    return tabla_df


def main(args_list=None):
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
    
    args = parser.parse_args(args_list)
    
    try:
        output_path = args.output
        
        if output_path is None:
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(repo_root, 'artifacts', 'graficos')
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(args.csv_file))[0]
            output_path = os.path.join(output_dir, f"{base_name}.png")
        
        tabla_df = parse_csv(args.csv_file)
        
        # Generar el gráfico
        plot_ganancias(tabla_df, output_path)

    except Exception as e:
        print(f"Error procesando archivo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
