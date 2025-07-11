import pandas as pd

# Leer solución
#filename = "modelo_dual_primal.sol"
filename = "soplex.sol"

with open(filename) as f:
	# status = f.readline() # status
	# o_value = f.readline() # objective value
	values = {}
	for line in f:
		comps = line.split()
		try:
			if comps[0][:2] == 'mu':
				values[comps[0]] = float(comps[1])
		except:
			pass

# x_{dp} = h_{dp} si c_p - M * mu_{dp} < 0 ; 0 c.c.

# Params
routes = range(5)
business_days_csv = "data/habiles.csv"
cost_routes_csv = "data/costo_rutas.csv"
# M
M = 30000000
# h_dp
business_days_df = pd.read_csv(business_days_csv, header=None)
business_days = {
	ridx: list(business_days_df.iloc[ridx]) for ridx in routes
}
# c_p
cost_routes_df = pd.read_csv(cost_routes_csv, header=None)
cost_routes = {
	ridx: float(cost_routes_df.iloc[ridx]) for ridx in routes
}

for key in values.keys():
	d,p = map(int,key.split('#')[1:])
	h_dp = business_days[p-1][d-1]
	c_p = cost_routes[p-1]
	mu_dp = values[key]
	if c_p - M*mu_dp < 0:
		if h_dp:
			print ("x_{}_{}, ".format(d,p), end='')
	elif c_p == M*mu_dp:
		print ("x_{}_{}, salió igual".format(d,p))#, end='')
