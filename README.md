## Experimento 2 CLI

`scripts/experimento_2.py` ahora acepta parámetros por línea de comandos para evitar editar el archivo cada vez.

### Uso básico

```bash
python scripts/experimento_2.py [opciones]
```

### Opciones

- `--threads INT` (por defecto: 8): cantidad de hilos.
- `--n-min INT` (por defecto: 1): mínimo de iteraciones por escenario.
- `--n-max INT` (por defecto: 0): máximo de iteraciones por escenario (0 = sin tope).
- `--solver STR` (por defecto: HiGHS): solver a utilizar (ej.: `cbc`, `HiGHS`, `fscip`).
- `--collection-mult FLOAT` (por defecto: 1.0): multiplicador de recaudación total.
- `--exp-id STR` (por defecto: `exp_test.json`): archivo JSON del experimento a leer/escribir.
- `--data-dir PATH` (por defecto: `./data/generated/`): directorio donde escribir los CSVs generados (`habiles.csv`, `rutas.csv`, `costo_rutas.csv`). El repo mantiene la carpeta con un `.gitkeep`, pero ignora sus contenidos.
- `--V-profile-max FLOAT` (por defecto: 2.0): Cuánto más grande es la recaudación máxima respecto a la mínima en el perfil V.
- `--V-max-day INT` (por defecto: 10): Qué día se realiza la máxima recaudación.
- `--route-cost-mult FLOAT` (por defecto: 1.5e-3): Multiplicador de costo de rutas.
- `--C-std FLOAT` (por defecto: .525): Desviación estándar perfil constante.
- `--V-std FLOAT` (por defecto: .3444): Desviación estándar perfil V.

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
- Las desviaciones estándar de los perfiles constantes y V ahora son configurables mediante `--C-std` y `--V-std`.

## Tabla de Resumen de Experimentos

`scripts/tabla_exp_1.py` genera tablas resumen con estadísticas (mean ± std) de experimentos.

### Uso básico

```bash
python scripts/tabla_exp_1.py [opciones]
```

### Opciones

- `--exp-id STR` (por defecto: `exp_test.json`): archivo JSON del experimento a procesar. Si es solo un nombre (sin ruta), se busca en `experiments/runs/`.
- `--output PATH` (opcional): archivo de texto donde escribir las tablas. Por defecto imprime a stdout. Si no se especifica pero se usa `--ods`, se genera automáticamente en `artifacts/reports/tabla_<exp-id>.txt`.
- `--ods PATH` (opcional): ruta del archivo ODS a generar. Requiere `odfpy` (instalar con `pip install odfpy`). Si no se especifica pero se usa `--output`, se puede generar automáticamente en `artifacts/reports/tabla_<exp-id>.ods`.
- `--output-dir PATH` (opcional): directorio donde guardar archivos. Por defecto: `artifacts/reports/`.

### Ejemplos

Imprimir a stdout:
```bash
python scripts/tabla_exp_1.py --exp-id exp_gurobi_durga_full_2025_11_5.json
```

Generar archivo de texto automáticamente:
```bash
python scripts/tabla_exp_1.py --exp-id exp_gurobi_durga_full_2025_11_5.json --output
```

Generar archivo de texto y ODS:
```bash
python scripts/tabla_exp_1.py --exp-id exp_gurobi_durga_full_2025_11_5.json --output --ods
```

El script genera tablas para cada perfil ("constant" y "V") con:
- Costos logísticos, financieros y totales para casos logísticos y financieros
- Ganancia (porcentaje de reducción de costo)
- Estadísticas: media ± desviación estándar
```