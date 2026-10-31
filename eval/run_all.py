#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = ["eval_institutions.py", "eval_triage.py", "eval_overlap.py"]


def main() -> int:
    failures = []
    for script in SCRIPTS:
        print(f"\n=== {script} ===", flush=True)
        result = subprocess.run([sys.executable, str(HERE / script)], check=False)
        if result.returncode != 0:
            failures.append(script)
    print("\ndone")
    if failures:
        print("failed:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
