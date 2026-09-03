import argparse, json, sys
from .prereg import seal_file, verify_file
from .runtime_guard import environment_report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sealedlab"); sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal", help="sha256 of a preregistration file (record it BEFORE running)"); s.add_argument("path")
    v = sub.add_parser("verify", help="verify a file against a recorded sha256"); v.add_argument("path"); v.add_argument("sha256")
    sub.add_parser("canary", help="run the runtime canaries and print the environment report")
    a = ap.parse_args(argv)
    if a.cmd == "seal":
        print(seal_file(a.path)); return 0
    if a.cmd == "verify":
        ok = verify_file(a.path, a.sha256); print("OK" if ok else "MISMATCH"); return 0 if ok else 1
    rep = environment_report(); print(json.dumps(rep, indent=1)); return 0 if rep["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
