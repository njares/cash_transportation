#!/usr/bin/env python3
"""
Genera tablas resumen de experimentos con estadísticas (mean ± std) para diferentes costos y ganancias.
"""
import json
import numpy as np
import argparse
import os
import sys


def ver_tabla(tabla, output_file=None):
    """Imprime una tabla formateada."""
    def _print(s):
        if output_file:
            output_file.write(s)
        else:
            print(s, end='')
    
    for row in tabla:
        ver_fila(row, output_file)
        _print('\n')


def ver_fila(fila, output_file=None):
    """Imprime una fila formateada."""
    def _print(s):
        if output_file:
            output_file.write(s)
        else:
            print(s, end='')
    
    for i in range(14):
        _print(f"{1e3*fila[i*2]:8.2G} | {1e3*fila[i*2+1]:8.2G} | ")
    _print(f"{100*fila[26]:8.2G} | {100*fila[27]:8.2G} %")


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


def generate_tables(exp_dict, output_file=None, ods_file=None):
    """
    Genera las tablas de resumen para cada perfil.
    
    Estructura esperada del exp_dict:
    - Llaves: rand_seed (string) -> perfil -> interés -> buzón -> [costo_total, costo_financiero_sin_interes]
    - Excluye '_meta' del conteo de seeds
    
    Args:
        exp_dict: Diccionario con los resultados del experimento
        output_file: Archivo de texto abierto para escritura (opcional)
        ods_file: Ruta del archivo ODS a generar (opcional)
    
    Returns:
        bool: True si ODS se generó exitosamente, False si falló o no se solicitó
    """
    def _print(s):
        if output_file:
            output_file.write(s)
        else:
            print(s)
    
    def _print_err(s):
        """Siempre imprime a stderr, no al archivo."""
        print(s, file=sys.stderr)
    
    # Get actual seed keys, excluding _meta
    seed_keys = [k for k in exp_dict.keys() if k != '_meta']
    N_exp = len(seed_keys)
    
    if N_exp == 0:
        _print("Error: No se encontraron seeds en el experimento (posiblemente vacío)")
        return
    
    # Store tables for ODS generation
    tables_data = {}
    
    # 2 tablas (una por perfil)
    # 40 filas (4 buzones × 10 intereses)
    # 28 columnas (14 pares mean±std, cada uno en 2 columnas)
    for perfil in ["constant", "V"]:
        # Tabla vacía
        tabla = np.zeros((40, 28))
        for buzon in range(4):
            for interes_anual in np.linspace(1, 10, 10):
                cur_fila = int(buzon*10 + (interes_anual-1))
                interes = (1+interes_anual/100)**(1/365)-1
                
                # caso logístico
                # costo logístico
                costos_logisticos_logistico = []
                for seed in seed_keys:
                    try:
                        costos_logisticos_logistico.append(exp_dict[seed][perfil]['0.0'][str(buzon)][0])
                    except (KeyError, IndexError):
                        continue
                
                if len(costos_logisticos_logistico) == 0:
                    continue
                
                mean = np.mean(costos_logisticos_logistico)
                std = np.std(costos_logisticos_logistico)
                tabla[cur_fila, 0] = mean
                tabla[cur_fila, 1] = std
                
                # costo financiero
                costos_financieros_logistico = []
                for seed in seed_keys:
                    try:
                        costos_financieros_logistico.append(exp_dict[seed][perfil]['0.0'][str(buzon)][1]*interes)
                    except (KeyError, IndexError):
                        continue
                
                mean = np.mean(costos_financieros_logistico)
                std = np.std(costos_financieros_logistico)
                tabla[cur_fila, 2] = mean
                tabla[cur_fila, 3] = std
                
                # costo total
                costos_total_logistico = [c_log + c_fin for c_log, c_fin in zip(costos_logisticos_logistico, costos_financieros_logistico)]
                mean = np.mean(costos_total_logistico)
                std = np.std(costos_total_logistico)
                tabla[cur_fila, 4] = mean
                tabla[cur_fila, 5] = std
                
                # caso financiero
                # costo financiero
                costos_financieros_financiero = []
                for seed in seed_keys:
                    try:
                        costos_financieros_financiero.append(exp_dict[seed][perfil][str(interes_anual)][str(buzon)][1]*interes)
                    except (KeyError, IndexError):
                        continue
                
                mean = np.mean(costos_financieros_financiero)
                std = np.std(costos_financieros_financiero)
                tabla[cur_fila, 16] = mean
                tabla[cur_fila, 17] = std
                
                # costo total
                costos_total_financiero = []
                for seed in seed_keys:
                    try:
                        costos_total_financiero.append(exp_dict[seed][perfil][str(interes_anual)][str(buzon)][0])
                    except (KeyError, IndexError):
                        continue
                
                mean = np.mean(costos_total_financiero)
                std = np.std(costos_total_financiero)
                tabla[cur_fila, 18] = mean
                tabla[cur_fila, 19] = std
                
                # costo logístico
                costos_logistico_financiero = [c_tot - c_fin for c_tot, c_fin in zip(costos_total_financiero, costos_financieros_financiero)]
                mean = np.mean(costos_logistico_financiero)
                std = np.std(costos_logistico_financiero)
                tabla[cur_fila, 14] = mean
                tabla[cur_fila, 15] = std
                
                # ganancia
                ganancias = [(c_log - c_fin) / c_log for c_log, c_fin in zip(costos_total_logistico, costos_total_financiero)]
                mean = np.mean(ganancias)
                std = np.std(ganancias)
                tabla[cur_fila, 26] = mean
                tabla[cur_fila, 27] = std
        
        tables_data[perfil] = tabla
        _print(perfil)
        _print('\n')
        ver_tabla(tabla, output_file)
    
    # Generate ODS if requested
    ods_success = False
    if ods_file:
        try:
            generate_ods(tables_data, ods_file)
            ods_success = True
            _print_err(f"Archivo ODS generado exitosamente: {ods_file}")
        except ImportError:
            _print_err("ERROR: No se pudo generar ODS. Instala 'odfpy' con: pip install odfpy")
        except Exception as e:
            _print_err(f"ERROR generando ODS: {e}")
            import traceback
            _print_err(traceback.format_exc())
    
    return ods_success


def generate_ods(tables_data, ods_file):
    """
    Genera un archivo ODS con las tablas usando odfpy.
    """
    from odf.opendocument import OpenDocumentSpreadsheet
    from odf.style import Style, TableCellProperties, TextProperties
    from odf.table import Table, TableRow, TableCell
    from odf.text import P
    
    doc = OpenDocumentSpreadsheet()
    
    # Define styles
    center_style = Style(name="Center", family="table-cell")
    doc.automaticstyles.addElement(center_style)
    
    for perfil, tabla in tables_data.items():
        table = Table(name=perfil)
        
        # Header row
        header_row = TableRow()
        headers = ["#B", "I(%)", "costo logístico", "", "costo financiero", "", "costo total", "",
                   "costo logístico", "", "costo financiero", "", "costo total", "", "ganancia (%)", ""]
        for h in headers:
            cell = TableCell()
            cell.addElement(P(text=h))
            cell.setAttribute('stylename', 'Center')
            header_row.addElement(cell)
        table.addElement(header_row)
        
        # Data rows
        for buzon in range(4):
            for interes_idx, interes_anual in enumerate(np.linspace(1, 10, 10)):
                row = TableRow()
                cur_fila = int(buzon*10 + interes_idx)
                
                # Buzon label (only on first row per buzón)
                if interes_idx == 0:
                    buzon_label = f"1/{buzon+1}" if buzon > 0 else "1"
                else:
                    buzon_label = ""
                cell = TableCell()
                cell.addElement(P(text=buzon_label))
                row.addElement(cell)
                cell = TableCell()
                cell.addElement(P(text=f"{interes_anual:.1f}"))
                row.addElement(cell)
                
                # Add data cells (mean and std in separate columns)
                for col_idx in range(0, 28, 2):
                    mean_val = tabla[cur_fila, col_idx]
                    std_val = tabla[cur_fila, col_idx + 1]
                    if col_idx == 26:  # ganancia (percentage)
                        text_mean = f"{100*mean_val:.2f}"
                        text_std = f"{100*std_val:.2f}"
                    else:
                        text_mean = f"{1e3*mean_val:.2G}"
                        text_std = f"{1e3*std_val:.2G}"
                    cell = TableCell()
                    cell.addElement(P(text=text_mean))
                    row.addElement(cell)
                    cell = TableCell()
                    cell.addElement(P(text=text_std))
                    row.addElement(cell)
                
                table.addElement(row)
        
        doc.spreadsheet.addElement(table)
    
    doc.save(ods_file)


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
        "--output",
        type=str,
        nargs='?',
        const='',
        default=None,
        help="Generar archivo de texto. Si se especifica sin argumento, auto-genera el nombre. Si se especifica con ruta, usa esa ruta. (por defecto: stdout)"
    )
    parser.add_argument(
        "--ods",
        type=str,
        nargs='?',
        const='',
        default=None,
        help="Generar archivo ODS. Si se especifica sin argumento, auto-genera el nombre. Si se especifica con ruta, usa esa ruta. (requiere 'odfpy': pip install odfpy)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directorio donde guardar archivos (por defecto: artifacts/reports/)"
    )
    args = parser.parse_args()
    
    try:
        exp_dict = parse_experiment(args.exp_id)
        
        # Determine output paths
        output_file = None
        ods_file = args.ods
        
        if args.output_dir:
            output_dir = args.output_dir
        else:
            repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_dir = os.path.join(repo_root, 'artifacts', 'reports')
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate base filename from exp_id if not specified
        base_name = os.path.splitext(os.path.basename(args.exp_id))[0]
        
        # Determine output paths
        if args.output is None and args.ods is None:
            # Default: print to stdout
            generate_tables(exp_dict, None, None)
        else:
            # Generate files
            # Handle --output: '' (empty string) means auto-generate, non-empty string means use that path
            if args.output == '':
                output_path = os.path.join(output_dir, f"tabla_{base_name}.txt")
            elif args.output:
                output_path = args.output
            else:
                output_path = None
            
            # Handle --ods: '' (empty string) means auto-generate, non-empty string means use that path
            if args.ods == '':
                ods_path = os.path.join(output_dir, f"tabla_{base_name}.ods")
            elif args.ods:
                ods_path = args.ods
            else:
                ods_path = None
            
            # If output is requested, we need at least a text file
            if output_path is None and ods_path:
                # If only ODS is requested, also generate text file
                output_path = os.path.join(output_dir, f"tabla_{base_name}.txt")
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    ods_success = generate_tables(exp_dict, f, ods_path)
                print(f"Archivo de texto generado: {output_path}", file=sys.stderr)
                if ods_path and not ods_success:
                    print(f"ADVERTENCIA: No se pudo generar el archivo ODS: {ods_path}", file=sys.stderr)
            else:
                # Only ODS requested (but this shouldn't happen with current logic)
                ods_success = generate_tables(exp_dict, None, ods_path)
                if ods_path and not ods_success:
                    print(f"ADVERTENCIA: No se pudo generar el archivo ODS: {ods_path}", file=sys.stderr)
                
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
