import json
import hashlib
import os
from pathlib import Path

Base = Path(__file__).resolve().parent
CFG = Base/"config.json"
Hashlist = Base / "hashlist.json"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def load_paths():
    if not CFG.exists():
        raise FileNotFoundError("Missing config.json")
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    return cfg.get("paths_to_watch", [])

def main():
    paths = load_paths()
    result = {}
    for p in paths:
        p_obj = Path(p)
        if not p_obj.exists():
            print(f"[WARN] Path not found, creating dummy: {p}")
            p_obj.parent.mkdir(parents=True, exist_ok=True)
            p_obj.write_bytes(b"TEST")
        result[str(p_obj)] = sha256_file(p_obj)
        print(f"[OK] {p}: {result[str(p_obj)]}")

    Hashlist.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved hashlist -> {Hashlist}")

if __name__ == "__main__":
    main()