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

    for i, col in enumerate(value_cols):
        plt.errorbar(
            plot_df['interes'],
            plot_df[col],
            yerr=plot_df[error_cols[i]],
            fmt='-o', # Format: line with circles
            label=labels[i], # Label for legend
            capsize=4 # Size of the error bar caps
        )
    
    plt.xlabel('I')
    plt.ylabel('Percentage')
    plt.title(f'Gain')
    plt.legend()
    plt.grid(True)
    plt.ylim(-5, 75)
    
    # Guardar
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Gráfico guardado en: {output_file}")


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
    
    args = parser.parse_args()
    
    try:
        output_path = args.output
        
        if output_path is None:
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(repo_root, 'artifacts', 'graficos')
            os.makedirs(output_dir, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(args.csv_file))[0]
            output_path = os.path.join(output_dir, f"{base_name}.png")
    
        tabla_df = pd.read_csv(args.csv_file)

        # Generar el gráfico
        plot_ganancias(tabla_df, output_path)

    except Exception as e:
        print(f"Error procesando archivo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import pdb;pdb.set_trace()
    main()
