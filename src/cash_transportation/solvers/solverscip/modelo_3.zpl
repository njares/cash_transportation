# Sets de índices

param nd:= read "data/datos_modelo.csv" as "1n"; # Cantidad de días
param np:= read "data/datos_modelo.csv" as "2n"; # Cantidad de rutas
param ns:= read "data/datos_modelo.csv" as "3n"; # Cantidad de sucursales

set D := {1..nd}; # Índices de días
set P := {1..np}; # Índices de rutas
set S := {1..ns}; # Índices de sucursales

# Parámetros

param M:= read "data/datos_modelo.csv" as "4n"; # Número grande para restricción 3
param i:= read "data/datos_modelo.csv" as "5n"; # interés diario

param e0[S] := read "data/e0.csv" as "n+"; # Efectivo inicial en la sucursal s
param r[S*D] := read "data/recaudacion.csv" as "n+"; # Recaudación de la sucursal s en el día d
param b[S] := read "data/buzon.csv" as "n+" comment "#"; # Capacidad del buzón de la sucursal s
param c[P] := read "data/costo_rutas.csv" as "n+"; # Costo de utilizar la ruta p
param m_aux[P*S] := read "data/rutas.csv" as "n+"; # Si la ruta p pasa por la sucursal s
param m[<s,p> in S*P] := m_aux[p,s]; # Si la sucursal s está en la ruta p
param h_aux[P*D] := read "data/habiles.csv" as "n+"; # Si la ruta p puede ser usada el día d
param h[<d,p> in D*P] := h_aux[p,d]; # Si el día d es hábil para la ruta p
set Dq := {read "data/ultimos_dias.csv" as "<n+>"}; # Índices de días con retiro obligatorio

# Variables

var x[D*P] binary; # Si se usa la ruta p en el día d
var e[S*D] real; # efectivo en sucursal s en el día d
var t[S*D*P] real; # Cantidad retirada de la sucursal s en el día d usando la ruta p

# Funcion objetivo

minimize costo: 
	sum <d> in D: (
		sum <p> in P: (
			c[p] * x[d,p]
		)
	)
	+
	i * sum <s> in S: (
		e0[s] + sum <d> in D-{nd}: e[s,d]
	)
	;

# Restricciones

subto rest11_0:
	forall <s,d> in S*(D-{1}):
		e[s,d] == e[s,d-1] + r[s,d] - sum <p> in P: (t[s,d,p]);

subto rest11_1:
	forall <s> in S:
		e[s,1] == e0[s] + r[s,1] - sum <p> in P: (t[s,1,p]);

subto rest12:
	forall <d,p> in D*P:
		sum <s> in S: (m[s,p]*t[s,d,p]) <= M * x[d,p];

subto rest13:
	forall <d,p> in D*P:
		sum <s> in S: ((1-m[s,p])*t[s,d,p]) == 0;

subto rest14:
	forall <s,d> in S*D:
		0 <= e[s,d] and
		e[s,d] <= b[s];

subto rest18_1:
	forall <s,d> in S*(D-{1}):
		sum <p> in P: t[s,d,p] <= e[s,d-1];

subto rest18_2:
	forall <s> in S:
		sum <p> in P: t[s,1,p] <= e0[s];

subto rest19:
	forall <s,d,p> in S*D*P:
		0 <= t[s,d,p];

subto rest20:
	forall <d,p> in D*P:
		x[d,p] <= h[d,p];

subto rest_last_q_days:
	forall <s> in S:
		1 <= sum <p,d> in P*Dq: m[s,p]*x[d,p];
