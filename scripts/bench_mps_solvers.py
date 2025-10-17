#!/usr/bin/env python
import argparse
import glob
import os
import time
from typing import Optional, Tuple, Any, Dict, List

import pulp


def load_problem_from_mps(mps_path: str, sense: str) -> pulp.LpProblem:
    sense = sense.lower()
    lp_sense = pulp.LpMinimize if sense in ("min", "minimize", "minimise") else pulp.LpMaximize
    loaded = pulp.LpProblem.fromMPS(mps_path, sense=lp_sense)
    # fromMPS may return (name, problem) or (problem, aux) depending on PuLP version; handle both
    if isinstance(loaded, tuple):
        # Find first element that is an LpProblem
        for item in loaded:
            if isinstance(item, pulp.LpProblem):
                return item
        # Fallback to first element
        return loaded[0]
    return loaded


def make_solver(name: str, threads: Optional[int], time_limit: Optional[float], msg: bool):
    lname = (name or "cbc").lower()
    if lname == "cbc":
        return pulp.PULP_CBC_CMD(msg=msg, presolve=1, threads=threads, timeLimit=time_limit)
    if lname == "fscip":
        return pulp.FSCIP_CMD(msg=msg)
    if lname == "scip":
        return pulp.SCIP_CMD(msg=msg)
    if lname == "gurobi":
        return pulp.GUROBI(msg=msg)
    if lname == "highs":
        return pulp.HiGHS(msg=msg)
    if lname == "cuopt":
        # Allow optional time limit for cuOpt if supported by your PuLP binding
        try:
            return pulp.CUOPT(msg=msg, timeLimit=time_limit)
        except TypeError:
            return pulp.CUOPT(msg=msg)
    return pulp.PULP_CBC_CMD(msg=msg, presolve=1, threads=threads, timeLimit=time_limit)


def solve_with_solver(prob: pulp.LpProblem, solver_name: str, threads: Optional[int], time_limit: Optional[float], msg: bool) -> Tuple[str, Optional[float], float]:
    solver = make_solver(solver_name, threads, time_limit, msg)
    start = time.perf_counter()
    status_code = prob.solve(solver)
    elapsed = time.perf_counter() - start
    status = pulp.LpStatus.get(status_code, str(status_code))
    obj_val = None
    try:
        obj_val = pulp.value(prob.objective)
    except Exception:
        obj_val = None
    return status, obj_val, elapsed


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark CBC vs CUOPT on all MPS files in a directory")
    parser.add_argument("problems_dir", nargs="?", default=os.path.join("cash_transportation", "problems"), help="Directory containing .mps files")
    parser.add_argument("--sense", default="min", help="Objective sense: min|max (default: min)")
    parser.add_argument("--threads", type=int, default=None, help="Threads for CBC")
    parser.add_argument("--cbc-time-limit", type=float, default=None, help="Time limit (s) for CBC")
    parser.add_argument("--cuopt-time-limit", type=float, default=None, help="Time limit (s) for CUOPT (if supported)")
    parser.add_argument("--msg", action="store_true", help="Enable solver logs")
    parser.add_argument("--pattern", default="*.mps", help="Glob pattern for files (default: *.mps)")
    parser.add_argument("--csv", default=None, help="Optional path to write CSV results")

    args = parser.parse_args()

    root = os.path.abspath(args.problems_dir)
    files = sorted(glob.glob(os.path.join(root, args.pattern)))
    if not files:
        print(f"No MPS files found in {root} matching {args.pattern}")
        return 2

    print(f"Found {len(files)} MPS files in {root}")

    rows: List[Dict[str, Any]] = []

    for mps_path in files:
        rel = os.path.relpath(mps_path, root)
        try:
            prob_cbc = load_problem_from_mps(mps_path, args.sense)
        except Exception as e:
            print(f"[SKIP] {rel}: failed to load MPS: {e}")
            continue

        # Solve with CBC
        status_cbc, obj_cbc, t_cbc = solve_with_solver(prob_cbc, "highs", args.threads, args.cbc_time_limit, args.msg)

        # Reload fresh problem for CUOPT to avoid any solver-side persistent state
        try:
            prob_cu = load_problem_from_mps(mps_path, args.sense)
        except Exception as e:
            print(f"[SKIP] {rel}: failed to reload MPS for cuOpt: {e}")
            continue

        status_cu, obj_cu, t_cu = solve_with_solver(prob_cu, "cuopt", None, args.cuopt_time_limit, args.msg)

        rows.append({
            "file": rel,
            "highs_status": status_cbc,
            "highs_obj": obj_cbc,
            "highs_time_s": t_cbc,
            "cuopt_status": status_cu,
            "cuopt_obj": obj_cu,
            "cuopt_time_s": t_cu,
        })

    # Print concise comparison table
    header = (
        f"{'file':60}  {'highs_status':10} {'highs_obj':>14} {'highs_s':>8}  "
        f"{'cuopt_status':11} {'cuopt_obj':>14} {'cuopt_s':>8}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        highs_obj_str = f"{r['highs_obj']:.6g}" if r['highs_obj'] is not None else 'NA'
        cuopt_obj_str = f"{r['cuopt_obj']:.6g}" if r['cuopt_obj'] is not None else 'NA'
        print(
            f"{r['file'][:60]:60}  {r['highs_status'][:10]:10} "
            f"{highs_obj_str:>14} {r['highs_time_s']:8.2f}  "
            f"{r['cuopt_status'][:11]:11} "
            f"{cuopt_obj_str:>14} {r['cuopt_time_s']:8.2f}"
        )

    if args.csv:
        import csv
        csv_path = os.path.abspath(args.csv)
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"CSV written to {csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


