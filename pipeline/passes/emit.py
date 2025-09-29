import json
from typing import Dict, Any
from pathlib import Path

def write_mer(mer: Dict[str, Any], out_path: str) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mer, f, ensure_ascii=False, indent=2)
