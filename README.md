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
- `--solver STR` (por defecto: cbc): solver a utilizar (ej.: `cbc`, `HiGHS`, `fscip`).
- `--collection-mult FLOAT` (por defecto: 1.0): multiplicador de recaudación total.
- `--exp-id STR` (por defecto: `exp_test.json`): archivo JSON del experimento a leer/escribir.
- `--data-dir PATH` (por defecto: `./data/generated/`): directorio donde escribir los CSVs generados (`habiles.csv`, `rutas.csv`, `costo_rutas.csv`). El repo mantiene la carpeta con un `.gitkeep`, pero ignora sus contenidos.

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


