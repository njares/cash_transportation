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


def plot_ganancias(csv_file, output_file=None):
    """
    Lee un archivo CSV y genera un gráfico de ganancias.
    
    Args:
        csv_file: Ruta al archivo CSV
        output_file: Ruta donde guardar la imagen (opcional)
    """
    # Leer el archivo CSV
    df = pd.read_csv(csv_file)
    
    # Extraer los datos necesarios
    buzones = df['buzon'].unique()
    intereses = df['interes'].unique()
    
    # Crear la figura
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Plot para cada buzón
    for buzon in buzones:
        data_buzon = df[df['buzon'] == buzon]
        # Ordenar por interés
        data_buzon = data_buzon.sort_values('interes')
        
        # Extraer ganancias (últimas dos columnas)
        ganancia_mean = data_buzon['ganancia_mean']
        ganancia_std = data_buzon['ganancia_std']
        
        # Convertir a porcentaje
        ganancia_mean = ganancia_mean * 100
        ganancia_std = ganancia_std * 100
        
        # Plot
        ax.errorbar(data_buzon['interes'], ganancia_mean, yerr=ganancia_std, 
                   marker='o', label=f'Buzón {buzon}', capsize=3)
    
    # Configurar el gráfico
    ax.set_xlabel('Interés Anual (%)')
    ax.set_ylabel('Ganancia (%)')
    ax.set_title('Comparación de Ganancias por Buzón e Interés')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Ajustar el diseño
    plt.tight_layout()
    
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
        
        # Generar el gráfico
        plot_ganancias(args.csv_file, output_path)
        
    except Exception as e:
        print(f"Error procesando archivo: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
