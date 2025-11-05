set presolving emphasis off
read modelo_dual.zpl
optimize
write solution modelo_dual_primal.sol
display dualsolution
