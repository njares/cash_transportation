import argparse
import os
import sys
_repo_root = os.path.dirname(os.path.abspath(__file__))
_repo_root = os.path.dirname(_repo_root)
_scripts_path = os.path.join(_repo_root, "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)
import pandas as pd
from experimento_2 import main as main_exp
from tabla_exp_1 import main as main_table
from plot_exp_1 import main as main_plot

parser = argparse.ArgumentParser()
parser.add_argument("--csv-file", type=str, default="experiments.csv", help="csv de experimentos")
args = parser.parse_args()

csv_file = args.csv_file

if os.path.sep not in csv_file and not csv_file.startswith('/'):
    # guardar por defecto en experiments/runs si es un nombre simple
    csv_file = os.path.join(_repo_root, 'data', csv_file)

# cargar csv con listado de experimentos
try:
    experiment_parameters = pd.read_csv(csv_file)
except Exception as e:
    print(f"Error leyendo archivo csv: {e}")


for row in experiment_parameters.itertuples():
    base_name = f"{row.Perfil}_{row.Std}_{row.Route_cost}_{row.V_max}_{row.V_day}"
    exp_args_list = ["--threads", "56",
        "--n-min", "3",
        "--n-max", "150",
        "--solver", "gurobi",
        "--exp-id", f"exp_{base_name}.json",
        "--V-profile-max", str(row.V_max),
        "--V-max-day", str(row.V_day),
        "--route-cost-mult", str(row.Route_cost),
        "--std", str(row.Std),
        "--profile", row.Perfil]
    # llamar a experimento_2.py para hacer cada experimento
    main_exp(args_list = exp_args_list)
    table_args_list = ["--exp-id", f"exp_{base_name}.json",
        "--csv-output"]
    main_table(args_list = table_args_list)
    # llamar a plot_exp_1.py para hacer los gráfico
    plot_args_list = ["--csv-file", f"tabla_exp_{base_name}.csv"] #, "--output", ]
    main_plot(args_list = plot_args_list)
