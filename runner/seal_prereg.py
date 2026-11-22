"""Seal a preregistration with external timestamps (study 3, E20; owner's request of 2026-11-08).

Writes OUT/pins.txt (sha256 of every pinned file, plus the image digest, interpreter and CLI version), then stamps
pins.txt three independent ways, none of which needs an account or discloses the content:
- RFC 3161 time-stamp tokens from freetsa.org, DigiCert and Sectigo (pins.txt.<tsa>.tsr, with the query .tsq);
- OpenTimestamps (pins.txt.ots), anchored in Bitcoin once the calendars aggregate (`ots upgrade` later).
Anyone can check: `openssl ts -verify -data pins.txt -in pins.txt.freetsa.tsr -CAfile freetsa-cacert.pem`, and
`ots verify pins.txt.ots`. The ledger entry that seals the preregistration attaches pins.txt and the tokens.

Usage: python3 seal_prereg.py OUT_DIR FILE... (paths relative to the repo root)
"""

import hashlib
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from run_trial import image_digest

ROOT = Path(__file__).resolve().parent.parent
TSA = {"freetsa": "https://freetsa.org/tsr", "digicert": "http://timestamp.digicert.com",
       "sectigo": "http://timestamp.sectigo.com"}  # fmt: skip
OTS = Path.home() / ".local" / "bin" / "ots"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main(out, files):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    paths = sorted({f for x in files for f in ([p for p in (ROOT / x).rglob("*") if p.is_file()]
                                                if (ROOT / x).is_dir() else [ROOT / x])})  # fmt: skip
    paths = [p for p in paths if "__pycache__" not in p.parts]
    digest = image_digest("eilikrineia-trial:cc2.1.319")  # same reader the trials use; raises if absent
    lines = [f"# study 3 pins (sha256), {datetime.now(timezone.utc).isoformat(timespec='seconds')}"]
    lines += [f"{sha(p)}  {p.relative_to(ROOT)}" for p in paths]
    lines += [f"image: eilikrineia-trial:cc2.1.319 {digest}", "interpreter: Python 3.11.18 /opt/homebrew/bin/python3.11",
              "claude-code: 2.1.319 (in the image)",
              "git: " + subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()]  # fmt: skip
    pins = out / "pins.txt"
    pins.write_text("\n".join(lines) + "\n")
    print(f"pins.txt: {len(paths)} files, sha256 {sha(pins)}")
    tsq = out / "pins.txt.tsq"
    subprocess.run(["openssl", "ts", "-query", "-data", str(pins), "-sha256", "-cert", "-out", str(tsq)], check=True,
                   capture_output=True)  # fmt: skip
    for name, url in TSA.items():
        req = urllib.request.Request(url, data=tsq.read_bytes(), headers={"Content-Type": "application/timestamp-query"})
        tsr = out / f"pins.txt.{name}.tsr"
        tsr.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        t = subprocess.run(["openssl", "ts", "-reply", "-in", str(tsr), "-text"], capture_output=True, text=True).stdout
        print(name, next((x.strip() for x in t.splitlines() if x.strip().startswith("Time stamp:")), "NO TIME"))
    cacert = out / "freetsa-cacert.pem"
    cacert.write_bytes(urllib.request.urlopen("https://freetsa.org/files/cacert.pem", timeout=60).read())
    v = subprocess.run(["openssl", "ts", "-verify", "-data", str(pins), "-in", str(out / "pins.txt.freetsa.tsr"),
                        "-CAfile", str(cacert)], capture_output=True, text=True)  # fmt: skip
    if "Verification: OK" not in v.stdout + v.stderr:
        sys.exit("freetsa token does not verify: " + (v.stdout + v.stderr)[-300:])
    print("freetsa verify: OK")
    subprocess.run([str(OTS), "stamp", str(pins)], check=True, capture_output=True)
    print("ots:", (out / "pins.txt.ots").exists())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
