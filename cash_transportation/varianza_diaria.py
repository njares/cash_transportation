import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize

data_dir = "../main/data"
input_excel = "DatosEntrada.xlsx"

input_excel_path = os.path.join(data_dir,input_excel)

df = pd.read_excel(input_excel_path,sheet_name=None)
sheets_name = list(df.keys())
recaudaciones = df[sheets_name[1]]

# sólo los números
recaudaciones = recaudaciones.iloc[3:,3:33].to_numpy()
recaudaciones = np.array(recaudaciones,dtype='float')

# la 87 es rara... son sólo nans...
recaudaciones = np.vstack([recaudaciones[:87,:],recaudaciones[88:,:]])

# sanity check
meses = recaudaciones.nonzero()[1].reshape(178,21)
mes_tipico = meses[0]
assert True == all([np.allclose(mes,mes_tipico) for mes in meses])

# Saco los dias sin recaudacion
recaudaciones = recaudaciones[:,mes_tipico]

# En las corridas la recaudación mensual total es "==1", así que uso esa "normalización" acá
# Esta normalizacion tiene que ser más parecida a lo que voy a usar despues...
recaudaciones_totales = np.sum(recaudaciones,axis=1)
recaudaciones = recaudaciones / np.tile(recaudaciones_totales,(21,1)).T

# Ver como si todas fueran constantes

# sólo me interesa la dispersión, que es lo que voy a sumar después
rec_constante_std = np.std(recaudaciones, axis=1)

plt.hist(rec_constante_std/(1/21))
plt.hist(rec_constante_std)
plt.show()
# la moda parece ser 0.025
# eso parece representar alrededor del 52% de la recaudación diaria promedio

# Ver como si fuera una cosa tipo V
np.argmax(recaudaciones,axis=1)
plt.hist(np.argmax(recaudaciones,axis=1))
plt.show()

# El día 7 es el más popular, ajustar contra ese día

# Hago un ajuste lineal a trozos

def piecewise_linear_periodic(x, a1, b1):
	a2 = -8*a1/13
	b2 = 7*(a1-a2) + b1
	return np.piecewise(x, [x <= 7], [lambda x : a1*x + b1, lambda x : a2*x + b2])

def piecewise_linear(x, a1, b1, a2, d):
	b2 = d*(a1-a2) + b1
	return np.piecewise(x, [x <= d], [lambda x : a1*x + b1, lambda x : a2*x + b2])

p_per , _ = optimize.curve_fit(piecewise_linear_periodic, np.arange(21), recaudaciones[0,:])
#p_lin , _ = optimize.curve_fit(piecewise_linear, np.arange(21), recaudaciones[0,:])

x = np.array(np.arange(21),dtype='float')

plt.plot(recaudaciones[0,:])
plt.plot(piecewise_linear_periodic(x,*p_per))
#plt.plot(piecewise_linear(x,*p_lin))
plt.show()

#parametros = [optimize.curve_fit(piecewise_linear, np.arange(21), recaudaciones[i,:])[0] for i in range(178)]
parametros = [optimize.curve_fit(piecewise_linear_periodic, np.arange(21), recaudaciones[i,:])[0] for i in range(178)]

recaudacion_ajuste = np.array([piecewise_linear_periodic(x,*parametros[i]) for i in range(178)])

# i=i+1
# plt.plot(recaudaciones[i,:])
# plt.plot(recaudacion_ajuste[i,:])
# plt.show()

recaudacion_V_normalizada = recaudaciones - recaudacion_ajuste

rec_V_std = np.std(recaudacion_V_normalizada, axis=1)

plt.hist(rec_V_std)
plt.show()

# la moda parece ser 0.01640
# eso parece representar un 34% de la recaudación diaria promedio
