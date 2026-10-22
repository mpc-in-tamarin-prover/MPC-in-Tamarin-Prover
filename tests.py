#!/usr/bin/env python3
"""Run the Tamarin models and report timing, memory and verdicts.

Changes against the first version:
  * models are addressed by name in a dict, so `semi-honest` can no longer
    silently run the GOD model (the old list index 4 was GOD, not semi_honest);
  * the process exit code is non-zero when a model fails to verify or Tamarin
    reports a falsified lemma, so the script is usable in CI;
  * every run prints the model path it actually executed.

Usage:
  python3 tests.py                # run every model
  python3 tests.py GOD            # one model (see MODELS below)
  python3 tests.py AllC           # the three complexity models only

Requires: tamarin-prover on PATH, GNU /usr/bin/time (Linux).
"""
import re
import shutil
import subprocess
import sys

MODELS = {
    "C2": "./complexity_measures/2_party/MPC.spthy",
    "C3": "./complexity_measures/3_party/MPC.spthy",
    "C4": "./complexity_measures/4_party/MPC.spthy",
    "semi-honest": "./semi_honest/MPC.spthy",
    "GOD": "./GOD/MPC.spthy",
    "Fairness": "./fairness/MPC.spthy",
    "Abort": "./sec_with_abort/MPC.spthy",
}
GROUPS = {"AllC": ["C2", "C3", "C4"]}

VERDICT_RE = re.compile(r"^\s{2}([A-Za-z0-9_]+)\s+\((?:all-traces|exists-trace)\):\s+(verified|falsified)")


def run_test(name):
    """Run one model. Returns True on success (no falsified lemma, exit code 0)."""
    model = MODELS[name]
    if shutil.which("tamarin-prover") is None:
        print("tamarin-prover not found on PATH", file=sys.stderr)
        return False
    time_bin = shutil.which("/usr/bin/time") or shutil.which("time")
    command = ["tamarin-prover", model, "--prove"]
    wrapper = [time_bin, "-v"] if time_bin and time_bin.endswith("/time") else []
    result = subprocess.run(wrapper + command, capture_output=True, text=True)

    print(f"### {name}: {model}")
    lines = result.stdout.splitlines()
    start = next((i for i, line in enumerate(lines) if "processing time:" in line), None)
    if start is None:
        print("'processing time:' not found — raw output below")
        print(result.stdout)
    else:
        for line in lines[start:]:
            print(line)

    falsified = [m.group(1) for line in lines for m in [VERDICT_RE.match(line)] if m and m.group(2) == "falsified"]
    if falsified:
        print("FALSIFIED LEMMAS: " + ", ".join(falsified))

    print("=" * 80)
    print("TIME / RESOURCE USAGE REPORT")
    print("=" * 80)
    match = re.search(r"(Command being timed:.*?Exit status:.*)", result.stderr, re.DOTALL)
    print(match.group(1) if match else "no /usr/bin/time report")
    print("=" * 80)
    print(f"EXIT CODE: {result.returncode}")
    print("=" * 80)
    return result.returncode == 0 and not falsified


def main(argv):
    if len(argv) == 1:
        targets = list(MODELS)
    else:
        targets = []
        for arg in argv[1:]:
            if arg in GROUPS:
                targets.extend(GROUPS[arg])
            elif arg in MODELS:
                targets.append(arg)
            else:
                print(f"unknown model: {arg}\nknown: {', '.join(MODELS)}; groups: {', '.join(GROUPS)}", file=sys.stderr)
                return 2

    failed = [name for name in targets if not run_test(name)]
    if failed:
        print("FAILED: " + ", ".join(failed), file=sys.stderr)
        return 1
    print(f"all {len(targets)} model(s) verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
