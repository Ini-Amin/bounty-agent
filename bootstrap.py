#!/usr/bin/env python3
"""Bootstrap checker untuk BOUNTY.

Cek dependency Python dan binary eksternal. Tanpa install otomatis.
"""
import argparse
import importlib.util
import json
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent


def load_manifest() -> dict:
    return json.loads((BASE / "tools.json").read_text(encoding="utf-8"))


def check_python(manifest: dict) -> dict:
    req_file = BASE / manifest.get("python_requirements", "requirements.txt")
    modules = []
    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name = line.split(">")[0].split("=")[0].split("<")[0].strip()
            modules.append(name)
    results = {}
    for mod in modules:
        try:
            results[mod] = bool(importlib.util.find_spec(mod))
        except Exception:
            results[mod] = False
    return results


def check_external(manifest: dict) -> dict:
    results = {}
    for item in manifest.get("external_recommended", []):
        results[item["name"]] = bool(shutil.which(item["name"]))
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="Cek dependency BOUNTY")
    ap.add_argument("--json", action="store_true", help="output JSON")
    a = ap.parse_args()

    manifest = load_manifest()
    data = {
        "python": check_python(manifest),
        "external": check_external(manifest),
    }
    if a.json:
        print(json.dumps(data, indent=2))
    else:
        print("Python dependencies:")
        for k, v in data["python"].items():
            print(f"  {'OK' if v else 'MISSING':7} {k}")
        print("\nExternal binaries (recommended):")
        for k, v in data["external"].items():
            print(f"  {'OK' if v else 'MISSING':7} {k}")
        print("\nInstall Python: pip install -r requirements.txt")
        print("Install external: lihat tools.json → external_recommended[].install")
    missing_py = [k for k, v in data["python"].items() if not v]
    return 1 if missing_py else 0


if __name__ == "__main__":
    sys.exit(main())
