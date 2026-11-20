#!/usr/bin/env bash
# install.sh — install the external tools listed in tools.json.
#   ./install.sh --check    (default: list missing tools only, no installs)
#   ./install.sh --install  (install the missing ones, best effort)
set -u
cd "$(dirname "$0")"

python3 - "$@" <<'PY'
import json
import shutil
import subprocess
import sys

force = "--install" in sys.argv
check = not force


def present(name):
    return shutil.which(name) is not None


missing = []
for t in json.load(open("tools.json")).get("external_recommended", []):
    name = t["name"]
    if present(name):
        print(f"OK       {name}")
    else:
        missing.append((name, t["install"]))

if not missing and check:
    print("all external tools present")
    sys.exit(0)

for name, install in missing:
    print(f"MISSING  {name}")
    if check:
        print(f"         run manually: {install}")
        continue
    print(f"         installing: {install}")
    try:
        subprocess.run(install.split(), check=False)
    except Exception as e:
        print(f"         failed: {e}")

print(f"missing: {len(missing)}")
PY
