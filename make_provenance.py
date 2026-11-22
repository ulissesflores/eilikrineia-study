"""Build or verify one SHA-256 chain hash over the code, the documents and the frozen data.

Usage
-----
    python make_provenance.py            # write output/provenance.json and output/hash-chain.md
    python make_provenance.py --verify   # recompute and compare with output/provenance.json

Hashed: every file under the sealed folders and every dated document at the root. Not
hashed: this repository's own packaging (README files, metadata, CI), the output folder and
anything that varies by machine. Raw trial folders, if a reader unpacks the raw archive under
``raw/``, are outside the sealed folders.
"""

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FOLDERS = (
    "runner",
    "runs",
    "prereg",
    "td",
    "template",
    "template3",
    "container",
    "patches",
    "rescore",
    "overclaim",
    "tests",
    "scripts",
)
ROOT_FILES = (
    "PREREGISTRATION*.md",
    "RESULTS*.md",
    "DEVIATION*.md",
    "POSTHOC*.md",
    "run_all.py",
    "make_provenance.py",
    "output/results.json",
)
SKIP = {"__pycache__", ".DS_Store", ".pytest_cache", ".ruff_cache"}


def files():
    """List the sealed files in a stable order.

    Returns
    -------
    list of pathlib.Path
        Paths relative to the repository root, sorted.
    """
    found = [p for d in FOLDERS for p in (ROOT / d).rglob("*") if p.is_file()]
    found += [p for g in ROOT_FILES for p in ROOT.glob(g)]
    return sorted(p.relative_to(ROOT) for p in found if not SKIP & set(p.parts))


def build():
    """Hash every sealed file and fold the hashes into one chain hash.

    Returns
    -------
    dict
        ``{"chain_hash": str, "files": {path: sha256}}``.
    """
    hashes = {p.as_posix(): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in files()}
    chain = hashlib.sha256()
    for path, digest in hashes.items():
        chain.update(f"{digest}  {path}\n".encode())
    return {"chain_hash": chain.hexdigest(), "files": hashes}


def main():
    """Write the seal, or verify it when ``--verify`` is given.

    Returns
    -------
    int
        Process exit code; 1 when verification fails.
    """
    now, out = build(), ROOT / "output"
    if "--verify" in sys.argv:
        old = json.loads((out / "provenance.json").read_text())
        names = set(old["files"]) | set(now["files"])
        changed = sorted(k for k in names if old["files"].get(k) != now["files"].get(k))
        if changed or old["chain_hash"] != now["chain_hash"]:
            print("provenance MISMATCH:", *(changed[:20] or ["chain_hash"]), sep="\n  ")
            return 1
        print(f"provenance verified: chain_hash {now['chain_hash']} ({len(now['files'])} files)")
        return 0
    out.mkdir(exist_ok=True)
    (out / "provenance.json").write_text(json.dumps(now, indent=1) + "\n")
    lines = [
        f"# Hash chain\n\n`chain_hash` (SHA-256): `{now['chain_hash']}`\n",
        f"{len(now['files'])} files.\n",
        "## Informational (NOT hashed)\n",
        "README files, REPRODUCIBILITY.md, docs/, assets/, licences, citation "
        "metadata, CI configuration, "
        "`output/`, caches. The raw trial archive carries its own checksum file.\n",
        "## Files\n",
        "```text",
    ]
    lines += [f"{d}  {p}" for p, d in now["files"].items()] + ["```", ""]
    (out / "hash-chain.md").write_text("\n".join(lines))
    print(f"chain_hash {now['chain_hash']} ({len(now['files'])} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
