# MODELO DUAL:
#
# 				minimizar						\sum_{d=1}^{n_d} \sum_{p=1}^{n_p} h_{dp} \alpha_{dp} 
# \alpha, \lambda, \mu, \nu, \zeta, \eta		+ \sum_{d=1}^{n_d}\sum_{s=1}^{n_s} r_{sd}\lambda_{sd} 
# 												+ \sum_{d=1}^{n_d}\sum_{s=1}^{n_s} b_s \zeta_{sd}
# 												+ \sum_{s=1}^{n_s} e_{s0} \lambda_{s1}
# 												+ \sum_{s=1}^{n_s} e_{s0} \eta_{s1}
# s.t.
# 	\alpha_{dp} + c_p - M mu_{dp} >= 0 ; d=1,...,n_d ; p=1,...,n_p
# 	i + \lambda_{sd} - \lambda_{s,d+1} + \zeta_{sd} - \eta_{s,d+1} >= 0 ; d=1,...,n_d-1 ; s=1,...,n_s (dual e_{sd})
# 	\lambda_{s n_d} + \zeta_{s n_d} >= 0 ; s=1,...,n_s (dual e_{s n_d})
# 	\lambda_{sd} + \eta_{sd} + m_{sp}\mu_{dp} + (1-m_{sp})\nu_{dp} >= 0 ; s=1,...,n_s ; d=1,...,n_d ; p=1,...,n_p (dual t_{sdp})
# 	\alpha_{dp}, \mu_{dp}, \nu_{dp}, \zeta_{sd}, \eta_{sd} >= 0 ; \lambda_{sd} libre

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

# set Dq := {read "data/ultimos_dias.csv" as "<n+>"}; # Índices de días con retiro obligatorio

# Variables

var alpha[D*P] real;
var lambda[S*D] real >= -infinity;
var mu[D*P] real;
var nu[D*P] real;
var zeta[S*D];
var eta[S*D];

# Funcion objetivo

minimize dual:
	sum <d> in D: (
		sum <p> in P: (
			h[d,p] * alpha[d,p]
		)
	)
	+
	sum <d> in D: (
		sum <s> in S: (
			r[s,d] * lambda[s,d]
		)
	)
	+
	sum <d> in D: (
		sum <s> in S: (
			b[s] * zeta[s,d]
		)
	)
	+
	sum <s> in S: (
		e0[s] * lambda[s,1]
	)
	+
	sum <s> in S: (
		e0[s] * eta[s,1]
	)
	;

# Restricciones

# \alpha_{dp} + c_p - M mu_{dp} >= 0 ; d=1,...,n_d ; p=1,...,n_p
subto rest_xdp:
	forall <d,p> in D*P:
		alpha[d,p] + c[p] - M * mu[d,p] >= 0 ;

# i + \lambda_{sd} - \lambda_{s,d+1} + \zeta_{sd} - \eta_{s,d+1} >= 0 ; d=1,...,n_d-1 ; s=1,...,n_s (dual e_{sd})
subto dual_esd:
	forall <d,s> in (D-{nd})*S:
		i + lambda[s,d] - lambda[s,d+1] + zeta[s,d] - eta[s,d+1] >= 0 ;

# 	\lambda_{s n_d} + \zeta_{s n_d} >= 0 ; s=1,...,n_s (dual e_{s n_d})
subto dual_esnd:
	forall <s> in S:
		lambda[s,nd] + zeta[s,nd] >= 0 ;

# 	\lambda_{sd} + \eta_{sd} + m_{sp}\mu_{dp} + (1-m_{sp})\nu_{dp} >= 0 ; s=1,...,n_s ; d=1,...,n_d ; p=1,...,n_p (dual t_{sdp})
subto dual_tsdp:
	forall <s,d,p> in S*D*P:
		lambda[s,d] + eta[s,d] + m[s,p] * mu[d,p] + (1-m[s,p]) * nu[d,p] >= 0;

# 	\alpha_{dp}, \mu_{dp}, \nu_{dp}, \zeta_{sd}, \eta_{sd} >= 0 ; \lambda_{sd} libre
subto alpha:
	forall <d,p> in D*P:
		alpha[d,p] >= 0 ;

subto mu:
	forall <d,p> in D*P:
		mu[d,p] >= 0 ;

subto nu:
	forall <d,p> in D*P:
		nu[d,p] >= 0 ;

subto zeta:
	forall <s,d> in S*D:
		zeta[s,d] >= 0 ;

subto eta:
	forall <s,d> in S*D:
		eta[s,d] >= 0 ;
