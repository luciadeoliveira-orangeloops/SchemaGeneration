import re
from typing import Dict, Any

def normalize_entity_name(name: str) -> str:
    return re.sub(r'[^A-Za-z0-9]', '', name[:1].upper() + name[1:])

def normalize_attr_name(name: str) -> str:
    if not name:
        return name
    s = re.sub(r'[^A-Za-z0-9]+', ' ', name).strip()
    parts = s.split()
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

def apply_aliases(name: str, glossary) -> str:
    aliases = {a for g in glossary for a in [g.get("term")] + g.get("aliases", []) if a}
    # if the name matches an alias, return the canonical term
    for g in glossary:
        if name == g.get("term") or name in (g.get("aliases") or []):
            return g.get("term")
    return name

def unify_naming(mer: Dict[str, Any], glossary) -> Dict[str, Any]:
    """Applies simple normalization to entities and attributes."""
    for e in mer.get("entities", []):
        e["name"] = normalize_entity_name(apply_aliases(e["name"], glossary))
        for a in e.get("attributes", []):
            a["name"] = normalize_attr_name(a["name"])
    for r in mer.get("relationships", []):
        r["from"] = normalize_entity_name(apply_aliases(r["from"], glossary))
        r["to"] = normalize_entity_name(apply_aliases(r["to"], glossary))
        if "fk" in r and r["fk"].get("attribute"):
            r["fk"]["attribute"] = normalize_attr_name(r["fk"]["attribute"])
    return mer
