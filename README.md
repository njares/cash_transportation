## Experimento 2 CLI

`scripts/experimento_2.py` ahora acepta parámetros por línea de comandos para evitar editar el archivo cada vez.

### Uso básico

```bash
python scripts/experimento_2.py [opciones]
```

### Opciones

- `--threads INT` (por defecto: 8): cantidad de hilos.
- `--n-min INT` (por defecto: 3): mínimo de iteraciones por escenario.
- `--n-max INT` (por defecto: 0): máximo de iteraciones por escenario (0 = sin tope).
- `--solver STR` (por defecto: HiGHS): solver a utilizar (ej.: `cbc`, `HiGHS`, `fscip`).
- `--collection-mult FLOAT` (por defecto: 1.0): multiplicador de recaudación total.
- `--exp-id STR` (por defecto: `exp_test.json`): archivo JSON del experimento a leer/escribir.
- `--data-dir PATH` (por defecto: `./data/generated/`): directorio donde escribir los CSVs generados (`habiles.csv`, `rutas.csv`, `costo_rutas.csv`). El repo mantiene la carpeta con un `.gitkeep`, pero ignora sus contenidos.
- `--V-profile-max FLOAT` (por defecto: 2.0): Cuánto más grande es la recaudación máxima respecto a la mínima en el perfil V.
- `--V-max-day INT` (por defecto: 10): Qué día se realiza la máxima recaudación.
- `--route-cost-mult FLOAT` (por defecto: 1.5e-3): Multiplicador de costo de rutas.
- `--profile STR` (por defecto: C): Perfil de recaudación (C: constante, V: wedge).
- `--std FLOAT` : Desviación estándar. Por defecto .525 para perfil constante y .3444 para perfil V.

### Ejemplos

Ejecutar con valores por defecto:

```bash
python scripts/experimento_2.py
```

Elegir solver y hilos:

```bash
python scripts/experimento_2.py --solver fscip --threads 12
```

Controlar iteraciones y ubicación de datos generados:

```bash
python scripts/experimento_2.py --n-min 1 --n-max 0 --data-dir ./data/generated/
```

Usar un archivo de experimento específico:

```bash
python scripts/experimento_2.py --exp-id exp_2025-10-23-01.json
```

Si `--exp-id` es solo un nombre (sin ruta), el archivo se crea/leé automáticamente en `experiments/runs/`. Si no existe, se crea con `{}`.

Además, el JSON mantiene tiempos de ejecución:
- En `['_meta']['total_runtime_seconds']`: tiempo acumulado total de todas las corridas agregadas.
- En `['<seed>']['_runtime_seconds']`: tiempo total invertido para esa seed.

### Recomendado: ejecutar con el paquete instalado en modo editable

```bash
pip install -e .
python scripts/experimento_2.py --solver cbc
```

Alternativamente, el script añade `src/` al `PYTHONPATH` automáticamente, por lo que también funciona sin instalación.

Notas:
- El umbral de `delta_std` se mantiene fijo en el código (no parametrizado).
- Más adelante se podrá agregar `--log-file` si se necesita persistir la salida.
- El perfil V ahora permite configurar la máxima recaudación y el día de pico.
- El costo de rutas ahora es configurable mediante `--route-cost-mult`.
- Las desviaciones estándar de los perfiles constantes y V ahora son configurables mediante `--std`.

## Tabla de Resumen de Experimentos

`scripts/tabla_exp_1.py` genera tablas resumen con estadísticas (mean y std) de experimentos.

### Uso básico

```bash
python scripts/tabla_exp_1.py [opciones]
```

### Opciones

- `--exp-id STR` (por defecto: `exp_test.json`): Archivo JSON del experimento a procesar. Si es solo un nombre (sin ruta), se busca en `experiments/runs/`.
- `--std-output` (opcional): Imprime la tabla en stdout. Por defecto no imprime a stdout.
- `--csv-output PATH` (opcional): Archivo de texto donde escribir la tabla. Si no se especifica ruta, se genera automáticamente en `artifacts/reports/tabla_<exp-id>.csv`. Si se especifica ruta, usa esa ruta.

### Ejemplos

Imprimir a stdout:
```bash
python scripts/tabla_exp_1.py --exp-id exp_gurobi_durga_full_2025_11_5.json --std-output
```

Generar archivo csv:
```bash
python scripts/tabla_exp_1.py --exp-id exp_gurobi_durga_full_2025_11_5.json --csv-output
```

El script genera tablas con:
- Costos logísticos, financieros y totales para casos logísticos y financieros
- Ganancia (porcentaje de reducción de costo)
- Estadísticas: media y desviación estándar

## Graficos a partir de las tablas

`scripts/plot_exp_1.py` Genera gráficos comparativos de ganancias a partir de tablas CSV.

### Uso básico

```bash
python scripts/plot_exp_1.py [opciones]
```

### Opciones

- `--csv-file STR` : Archivo CSV con los datos de ganancia.
- `--output STR` (opcional): Archivo de salida para guardar la imagen. Por defecto guarda en `artifacts/graficos/<csv-file-basename>.png`.

### Ejemplos

Generar archivo png:
```bash
python scripts/plot_exp_1.py --exp-id exp_gurobi_durga_full_2025_11_5.json
```
