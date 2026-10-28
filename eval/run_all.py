#!/usr/bin/env python3
import subprocess
import sys


def main():
    for script in ["eval_institutions.py", "eval_triage.py", "eval_overlap.py"]:
        try:
            subprocess.run([sys.executable, script], check=False)
        except Exception as e:
            print(e)
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
