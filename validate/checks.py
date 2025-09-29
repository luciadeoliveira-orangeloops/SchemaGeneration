from typing import Dict, Any

def names_unique(mer: Dict[str, Any]) -> bool:
    seen = set()
    for e in mer.get("entities", []):
        n = e.get("name")
        if n in seen: return False
        seen.add(n)
    return True
