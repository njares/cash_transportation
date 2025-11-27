# Experimentos

## Descripción General

Este directorio contiene los resultados de experimentos ejecutados con diferentes configuraciones.

## Archivos de Experimentos

| Nombre del Archivo | Fecha | Solver | V Max | V Day | Route cost | C Std | V Std | Descripción |
|--------------------|-------|--------|-------|-------|------------|-------|-------|-------------|
| `exp_2025-11-16_gurobi_2.0_10_1.5e-3_0.525_0.3444.json` | 2025-11-16 | gurobi | 2.0 | 10 | 1.5e-3 | 0.525 | 0.3444 | Caso base con ruido |
| `exp_2025-11-16_gurobi_5.0_10_1.5e-3_0.525_0.3444.json` | 2025-11-16 | gurobi | 5.0 | 10 | 1.5e-3 | 0.525 | 0.3444 | Pico de recaudación máxima 5 veces más grande que la recaudación mínima |
| `exp_2025-11-16_gurobi_2.0_20_1.5e-3_0.525_0.3444.json` | 2025-11-16 | gurobi | 2.0 | 20 | 1.5e-3 | 0.525 | 0.3444 | Día de recaudación máxima en el día 20 |
| `exp_2025-11-16_gurobi_2.0_10_3.0e-3_0.525_0.3444.json` | 2025-11-16 | gurobi | 2.0 | 10 | 3.0e-3 | 0.525 | 0.3444 | Costo de rutas doble |
| `exp_2025-11-17_gurobi_2.0_10_1.5e-3_0.000_0.0000.json` | 2025-11-17 | gurobi | 2.0 | 10 | 1.5e-3 | 0.000 | 0.0000 | Caso base sin ruido |
| `exp_2025-11-17_gurobi_2.0_10_1.5e-3_0.250_0.2500.json` | 2025-11-17 | gurobi | 2.0 | 10 | 1.5e-3 | 0.250 | 0.2500 | Caso con ruido 25 % |
| `exp_2025-11-17_gurobi_2.0_10_1.5e-3_0.500_0.5000.json` | 2025-11-17 | gurobi | 2.0 | 10 | 1.5e-3 | 0.500 | 0.5000 | Caso con ruido 50 %  |
| `exp_2025-11-17_gurobi_2.0_10_1.5e-3_0.750_0.7500.json` | 2025-11-17 | gurobi | 2.0 | 10 | 1.5e-3 | 0.750 | 0.7500 | Caso con ruido 75 % |
| `exp_2025-11-17_gurobi_2.0_10_1.5e-3_1.000_1.0000.json` | 2025-11-17 | gurobi | 2.0 | 10 | 1.5e-3 | 1.000 | 1.0000 | Caso con ruido 100 % |

## Descripción de Parámetros

- `collection_mult`: Multiplicador de recaudación total.
- `V_profile_max`: Cuánto más grande es la recaudación máxima respecto a la mínima en el perfil V.
- `V_max_day`: Qué día se realiza la máxima recaudación.
- `route_cost_mult`: Multiplicador de costo de rutas.
- `C_std`: Desviación estándar perfil constante.
- `V_std`: Desviación estándar perfil V.

## Ejemplo:

`exp_2025-11-16_gurobi_2.0_10_1.5e-3_0.525_0.3444.json`

### Explicación de los Componentes

- `exp_`: Prefijo estándar para identificar archivos de experimentos.
- `2025-11-16`: Fecha del experimento (formato YYYY-MM-DD).
- `gurobi`: Solver utilizado.
- `2.0`: Valor de --V-profile-max.
- `10`: Valor de --V-max-day.
- `1.5e-3`: Valor de --route-cost-mult.
- `0.525`: Valor de --C-std.
- `0.3444`: Valor de --V-std.
 
