"""Run local checks once, or continuously on source updates with --watch."""
from pathlib import Path
import argparse
import hashlib
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
def run():
    (ROOT/"artifacts").mkdir(exist_ok=True)
    for args in ([sys.executable,"-m","compileall","-q","app","tests"],
                 [sys.executable,"-m","pytest","-q","--cov=app","--cov=migrations","--cov-report=term-missing","--cov-report=xml:artifacts/coverage.xml","--cov-report=json:artifacts/coverage.json","--cov-fail-under=85","--junitxml=artifacts/tests.xml"]):
        result=subprocess.run(args,cwd=ROOT)
        if result.returncode: return result.returncode
    return 0
def fingerprint():
    files=[*ROOT.glob("app/**/*.py"),*ROOT.glob("app/static/*"),*ROOT.glob("app/templates/*"),
           *ROOT.glob("tests/*.py"),*ROOT.glob("requirements*.txt")]
    return hashlib.sha256(b"".join(p.read_bytes() for p in sorted(files))).hexdigest()
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--watch",action="store_true");args=parser.parse_args()
    result=run()
    if not args.watch: raise SystemExit(result)
    previous=fingerprint()
    print("Watching source files; press Ctrl+C to stop.",flush=True)
    try:
        while True:
            time.sleep(1)
            current=fingerprint()
            if current!=previous:
                previous=current
                print("Change detected: rerunning checks.",flush=True)
                run()
    except KeyboardInterrupt: pass

