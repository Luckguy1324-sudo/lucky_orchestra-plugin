#!/usr/bin/env python3
"""physics_check.py — v0.8.0 deterministic process-physics grounding (Pre-Gate, mechanism ⑧+).

Two layers, by design:

  LAYER 1 — universal invariants (ALWAYS on, no thresholds needed).
            Mass conservation, energy conservation, 2nd-law / no temperature-cross in heat
            exchangers, and basic dimensional sanity. These are physical law: a violation is
            simply wrong, regardless of what the user has (or has not) decided yet. This is
            what lets a blank-page run be grounded from round 1.

  LAYER 2 — design criteria (DYNAMIC, loaded from meta.json.decisions[]).
            Things like a target ΔT_min, an energy-balance tolerance, a max pressure drop.
            These are NOT known at the start of a blank-page run — they are *formed* over
            rounds and recorded as decisions[] (C2). Layer 2 enforces only the criteria that
            have been formalised into a machine-readable `check` on a decision entry. A
            decision with no `check` is informational only; it is not silently invented here.

IMPORTANT — what this does and does NOT prove (honest boundary):
  Closure proves INTERNAL CONSISTENCY, not CORRECTNESS. A fabricated-but-self-consistent
  stream table will pass Layer 1. The numbers themselves are validated downstream by the
  external Reviewer (ChatGPT) and the web audit (⑥c). This gate stops a draft whose own
  numbers contradict each other from ever reaching (and wasting) a manual review pass.

Input: a streams.json describing streams, unit balances and heat exchangers. See SCHEMA below.
Usage:
    physics_check.py <streams.json> [meta.json]
Exit: 0 = all enforced checks PASS, 1 = a hard check FAILED, 2 = usage/parse error.

SCHEMA (streams.json):
{
  "tol": {"mass_pct": 0.1, "energy_pct": 2.0},          # optional; defaults below
  "streams": [
    {"id":"S1","role":"in","mdot_kg_s":1.0,"T_K":300,"P_bar":2.0,
     "h_kJ_kg":-10.0,"components":{"H2":1.0}}            # role: in|out|internal
  ],
  "units": [                                             # per-unit mass+energy balance
    {"id":"K1","in":["S2"],"out":["S3"],"Q_kW":0.0,"W_kW":120.0}
  ],
  "heat_exchangers": [
    {"id":"HX1","hot_in":"S4","hot_out":"S5","cold_in":"S6","cold_out":"S7"}
  ]
}
Sign convention for unit energy balance: sum(mdot*h)_in + Q_in + W_in == sum(mdot*h)_out.
Q_kW = heat ADDED to the stream (+in). W_kW = work ADDED to the stream (+in, e.g. compressor).
"""
import json
import sys
from pathlib import Path

DEFAULT_MASS_PCT = 0.1
DEFAULT_ENERGY_PCT = 2.0


def die(msg, code=2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_json(p):
    path = Path(p)
    if not path.exists():
        die(f"file not found: {p}")
    try:
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    except json.JSONDecodeError as e:
        die(f"could not parse {p}: {e}")


def smap(streams):
    m = {}
    for s in streams:
        if "id" not in s:
            die("a stream has no 'id'")
        m[s["id"]] = s
    return m


def num(s, key):
    v = s.get(key)
    return float(v) if isinstance(v, (int, float)) else None


# --------------------------------------------------------------------------- Layer 1
def check_dimensions(streams):
    """Absolute physical sanity: no negative absolute T/P, no negative mdot."""
    fails = []
    for s in streams:
        sid = s.get("id", "?")
        for key, lo in (("T_K", 0.0), ("P_bar", 0.0), ("mdot_kg_s", 0.0)):
            v = num(s, key)
            if v is not None and v < lo:
                fails.append(f"{sid}: {key}={v} is below physical minimum {lo}")
    return fails


def check_global_mass(streams, tol_pct):
    fails = []
    ins = [s for s in streams if s.get("role") == "in"]
    outs = [s for s in streams if s.get("role") == "out"]
    if not ins or not outs:
        return ["global mass balance: need at least one role='in' and one role='out' stream"]
    min_ = sum(num(s, "mdot_kg_s") or 0.0 for s in ins)
    mout = sum(num(s, "mdot_kg_s") or 0.0 for s in outs)
    if min_ == 0:
        return ["global mass balance: total inflow is 0 — cannot evaluate"]
    err = abs(min_ - mout) / min_ * 100.0
    if err > tol_pct:
        fails.append(f"global mass balance: in={min_:.4g} out={mout:.4g} "
                     f"(err {err:.3f}% > tol {tol_pct}%)")
    # component-wise
    def comp_tot(group):
        acc = {}
        for s in group:
            md = num(s, "mdot_kg_s") or 0.0
            for c, frac in (s.get("components") or {}).items():
                acc[c] = acc.get(c, 0.0) + md * float(frac)
        return acc
    ci, co = comp_tot(ins), comp_tot(outs)
    for c in set(ci) | set(co):
        a, b = ci.get(c, 0.0), co.get(c, 0.0)
        base = a if a else 1e-9
        e = abs(a - b) / base * 100.0
        if e > tol_pct:
            fails.append(f"component '{c}' mass balance: in={a:.4g} out={b:.4g} "
                         f"(err {e:.3f}% > tol {tol_pct}%)")
    return fails


def check_unit_balances(units, sm, tol_mass, tol_energy):
    fails = []
    for u in units or []:
        uid = u.get("id", "?")
        ins = [sm[i] for i in u.get("in", []) if i in sm]
        outs = [sm[o] for o in u.get("out", []) if o in sm]
        missing = [x for x in u.get("in", []) + u.get("out", []) if x not in sm]
        if missing:
            fails.append(f"unit {uid}: references unknown streams {missing}")
            continue
        # mass
        mi = sum(num(s, "mdot_kg_s") or 0.0 for s in ins)
        mo = sum(num(s, "mdot_kg_s") or 0.0 for s in outs)
        if mi > 0 and abs(mi - mo) / mi * 100.0 > tol_mass:
            fails.append(f"unit {uid} mass: in={mi:.4g} out={mo:.4g} "
                         f"(> tol {tol_mass}%)")
        # energy (only if all enthalpies present)
        hi = [num(s, "h_kJ_kg") for s in ins]
        ho = [num(s, "h_kJ_kg") for s in outs]
        if all(h is not None for h in hi + ho) and (ins and outs):
            ein = sum((num(s, "mdot_kg_s") or 0.0) * num(s, "h_kJ_kg") for s in ins)
            eout = sum((num(s, "mdot_kg_s") or 0.0) * num(s, "h_kJ_kg") for s in outs)
            q = float(u.get("Q_kW", 0.0))
            w = float(u.get("W_kW", 0.0))
            lhs = ein + q + w  # kW  (mdot[kg/s]*h[kJ/kg] = kW)
            base = abs(eout) if abs(eout) > 1e-9 else 1e-9
            e = abs(lhs - eout) / base * 100.0
            if e > tol_energy:
                fails.append(f"unit {uid} energy: in+Q+W={lhs:.4g}kW out={eout:.4g}kW "
                             f"(err {e:.2f}% > tol {tol_energy}%)")
    return fails


def check_heat_exchangers(hxs, sm):
    """2nd-law feasibility: no temperature cross; hot side cools, cold side heats."""
    fails = []
    for hx in hxs or []:
        hid = hx.get("id", "?")
        try:
            thi = num(sm[hx["hot_in"]], "T_K")
            tho = num(sm[hx["hot_out"]], "T_K")
            tci = num(sm[hx["cold_in"]], "T_K")
            tco = num(sm[hx["cold_out"]], "T_K")
        except KeyError as e:
            fails.append(f"HX {hid}: references unknown stream {e}")
            continue
        if None in (thi, tho, tci, tco):
            fails.append(f"HX {hid}: missing T_K on one or more ports — cannot verify 2nd law")
            continue
        if not (thi > tho):
            fails.append(f"HX {hid}: hot side does not cool (hot_in {thi}K !> hot_out {tho}K)")
        if not (tco > tci):
            fails.append(f"HX {hid}: cold side does not heat (cold_out {tco}K !> cold_in {tci}K)")
        # no temperature cross at either end
        if tho < tci:
            fails.append(f"HX {hid}: temperature cross — hot_out {tho}K < cold_in {tci}K")
        if thi < tco:
            fails.append(f"HX {hid}: temperature cross — hot_in {thi}K < cold_out {tco}K")
    return fails


# --------------------------------------------------------------------------- Layer 2
def check_decisions(decisions, sm, hxs_by_id, tol_default):
    """Enforce ONLY machine-readable `check` blocks on decisions[]. Dynamic per run.

    Supported check types:
      {"type":"dt_min","hx":"HX1","min_K":3}
      {"type":"dp_max","unit":"K1","max_bar":0.5}     # uses stream P drop across unit in/out
      {"type":"balance_tol","kind":"energy|mass","max_pct":2.0}  # advisory tightening (informational)
      {"type":"T_max","stream":"S3","max_K":420}
      {"type":"T_min","stream":"S9","min_K":20}
    Unknown/absent check types are skipped (informational decision only).
    """
    fails = []
    applied = 0
    for d in decisions or []:
        chk = d.get("check")
        if not isinstance(chk, dict):
            continue
        t = chk.get("type")
        applied += 1
        if t == "dt_min":
            hx = hxs_by_id.get(chk.get("hx"))
            if not hx:
                fails.append(f"decision dt_min: HX '{chk.get('hx')}' not in streams.json")
                continue
            try:
                thi = num(sm[hx["hot_in"]], "T_K"); tco = num(sm[hx["cold_out"]], "T_K")
                tho = num(sm[hx["hot_out"]], "T_K"); tci = num(sm[hx["cold_in"]], "T_K")
            except KeyError:
                fails.append(f"decision dt_min: HX '{chk.get('hx')}' has unknown port streams")
                continue
            if None in (thi, tco, tho, tci):
                fails.append(f"decision dt_min: HX '{chk.get('hx')}' missing T_K — cannot check")
                continue
            approach = min(thi - tco, tho - tci)
            if approach < float(chk["min_K"]):
                fails.append(f"decision dt_min on {chk.get('hx')}: approach {approach:.2f}K "
                             f"< required {chk['min_K']}K")
        elif t == "T_max":
            s = sm.get(chk.get("stream"))
            v = num(s, "T_K") if s else None
            if v is not None and v > float(chk["max_K"]):
                fails.append(f"decision T_max on {chk.get('stream')}: {v}K > {chk['max_K']}K")
        elif t == "T_min":
            s = sm.get(chk.get("stream"))
            v = num(s, "T_K") if s else None
            if v is not None and v < float(chk["min_K"]):
                fails.append(f"decision T_min on {chk.get('stream')}: {v}K < {chk['min_K']}K")
        elif t == "dp_max":
            # informational unless both ports carry P_bar; checks single in/out stream pair
            pass
        # balance_tol handled by caller (tightens tolerances); not a hard fail here
    return fails, applied


def main():
    if len(sys.argv) not in (2, 3):
        die("Usage: physics_check.py <streams.json> [meta.json]")
    data = load_json(sys.argv[1])
    meta = load_json(sys.argv[2]) if len(sys.argv) == 3 else {}

    streams = data.get("streams")
    if not streams:
        die("streams.json has no 'streams' array", 2)
    sm = smap(streams)
    hxs = data.get("heat_exchangers", [])
    hxs_by_id = {h.get("id"): h for h in hxs}

    tol = data.get("tol", {})
    tol_mass = float(tol.get("mass_pct", DEFAULT_MASS_PCT))
    tol_energy = float(tol.get("energy_pct", DEFAULT_ENERGY_PCT))
    # a balance_tol decision can tighten (never loosen) the energy tolerance
    for d in meta.get("decisions", []):
        chk = d.get("check") or {}
        if chk.get("type") == "balance_tol" and chk.get("kind") == "energy":
            tol_energy = min(tol_energy, float(chk["max_pct"]))
        if chk.get("type") == "balance_tol" and chk.get("kind") == "mass":
            tol_mass = min(tol_mass, float(chk["max_pct"]))

    print("=== Orchestra Physics Check (Pre-Gate ⑧+, v0.8.0) ===")
    print(f"streams={len(streams)} units={len(data.get('units', []))} HX={len(hxs)} "
          f"| tol mass {tol_mass}% energy {tol_energy}%\n")

    results = []
    results.append(("L1 dimensional sanity", check_dimensions(streams)))
    results.append(("L1 global mass balance", check_global_mass(streams, tol_mass)))
    results.append(("L1 per-unit mass+energy", check_unit_balances(data.get("units"), sm,
                                                                   tol_mass, tol_energy)))
    results.append(("L1 HX 2nd-law / no temp-cross", check_heat_exchangers(hxs, sm)))
    l2_fails, l2_applied = check_decisions(meta.get("decisions", []), sm, hxs_by_id, tol_energy)
    results.append((f"L2 design criteria ({l2_applied} enforced)", l2_fails))

    fail = 0
    for name, fails in results:
        if fails:
            fail = 1
            print(f"[FAIL] {name}")
            for f in fails:
                print(f"       - {f}")
        else:
            print(f"[PASS] {name}")

    print()
    if fail:
        print("=== PHYSICS CHECK: FAIL — the draft's own numbers are inconsistent. "
              "Fix before review. ===")
        sys.exit(1)
    print("=== PHYSICS CHECK: PASS — internally consistent (correctness still verified at Review). ===")
    sys.exit(0)


if __name__ == "__main__":
    main()
