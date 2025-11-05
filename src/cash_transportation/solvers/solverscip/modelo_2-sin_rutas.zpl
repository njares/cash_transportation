# Sets de índices

param n:= read "datos_modelo.csv" as "1n"; # Cantidad de sucursales
param m:= read "datos_modelo.csv" as "2n"; # Cantidad de días

set S := {1..n}; # Índices de sucursales
set D := {1..m}; # Índices de días

# Parámetros

param M:= read "datos_modelo.csv" as "3n"; # Número grande para restricción 2

param r[S*D] := read "recaudaciones.csv" as "n+"; # Recaudación de la sucursal s en el día d
param b[S] := read "buzones.csv" as "n+"; # Capacidad del buzón de la sucursal s

# Variables

var x[S*D] binary; # Si la sucursal s tiene retiro el día d
var e[S*D] real; # Stock dinero en sucursal s en el día d
var q[S*D] real # Cantidad de dinero retirado de la sucursal s en el d{ia d

# Funcion objetivo

minimize costo: 
	sum <d> in D: (
		sum <s> in S: (
			x[s,d]
		)
	);

# Restricciones

subto rest1:
	forall <s,d> in S*D:
		e[s,d] == e[s,d-1] + r[s,d] - q[s,d-1];

subto rest2:
	forall <s,d> in S*D:
		q[s,d] <= M * x[s,d];

subto rest3:
	forall <s,d> in S*D:
		0 <= e[s,d] and
		e[s,d] <= b[s];

subto rest4:
	forall <s,d> in S*D:
		0 <= q[s,d] and
		q[s,d] <= e[s,d-1];

subto rest5:
	forall <s> in S:
		x[s,30] == 1;
