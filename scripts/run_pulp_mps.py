#!/usr/bin/env python
import argparse
import os
import sys
from typing import Optional

import pulp


def make_solver(name: str, threads: Optional[int], time_limit: Optional[float], msg: bool):
    name = (name or "cbc").lower()
    if name == "cbc":
        return pulp.PULP_CBC_CMD(msg=msg, presolve=1, threads=threads, timeLimit=time_limit)
    if name == "fscip":
        return pulp.FSCIP_CMD(msg=msg)
    if name == "scip":
        return pulp.SCIP_CMD(msg=msg)
    if name == "gurobi":
        return pulp.GUROBI(msg=msg)
    if name == "cuopt":
        return pulp.CUOPT(msg=msg, timeLimit=60)
    if name == "highs":
        return pulp.HiGHS(msg=msg)
    print(f"WARNING: Unknown solver '{name}', defaulting to CBC")
    return pulp.PULP_CBC_CMD(msg=msg, presolve=1, threads=threads, timeLimit=time_limit)


def load_problem_from_mps(path: str, sense: str):
    sense = sense.lower()
    lp_sense = pulp.LpMinimize if sense in ("min", "minimize", "minimise") else pulp.LpMaximize
    # PuLP supports reading MPS via fromMPS. Some versions may return (problem, aux_data).
    loaded = pulp.LpProblem.fromMPS(path, sense=lp_sense)
    if isinstance(loaded, tuple) and len(loaded) >= 1:
        return loaded[1]
    return loaded


def main() -> int:
    parser = argparse.ArgumentParser(description="Solve an MPS model with PuLP")
    parser.add_argument("mps", help="Path to .mps model")
    parser.add_argument("--solver", default="cbc", help="cbc|fscip|scip|gurobi|cuopt (default: cbc)")
    parser.add_argument("--sense", default="min", help="Objective sense: min|max (default: min)")
    parser.add_argument("--threads", type=int, default=None, help="Threads (CBC only)")
    parser.add_argument("--time-limit", type=float, default=None, help="Time limit seconds (CBC only)")
    parser.add_argument("--msg", action="store_true", help="Enable solver messages")
    parser.add_argument("--print-vars", action="store_true", help="Print non-zero variable values")

    args = parser.parse_args()

    mps_path = os.path.abspath(args.mps)
    if not os.path.exists(mps_path):
        print(f"ERROR: MPS file not found: {mps_path}")
        return 2

    try:
        prob = load_problem_from_mps(mps_path, args.sense)
    except Exception as e:
        print(f"ERROR: Failed to load MPS: {e}")
        return 3

    solver = make_solver(args.solver, args.threads, args.time_limit, args.msg)

    status_code = prob.solve(solver)
    status = pulp.LpStatus.get(status_code, str(status_code))
    print(f"Status: {status}")

    try:
        obj_val = pulp.value(prob.objective)
        print(f"Objective: {obj_val}")
    except Exception:
        pass

    if args.print_vars:
        for v in prob.variables():
            try:
                val = v.varValue
            except Exception:
                val = None
            if val is not None and abs(val) > 1e-12:
                print(f"{v.name} = {val}")

    return 0 if status_code == 1 else 1


if __name__ == "__main__":
    sys.exit(main())
