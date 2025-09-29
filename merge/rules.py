from typing import Dict, Any

def resolve_cardinality(rel: Dict[str, Any], doc_rules) -> Dict[str, Any]:
    """If there is an explicit rule from documents, use it; otherwise, keep the inferred one."""
    for rule in doc_rules:
        if rule.get("kind") == "cardinality" and \
           rule.get("from") == rel.get("from") and rule.get("to") == rel.get("to"):
            rel["type"] = rule.get("type", rel.get("type"))
            rel.setdefault("sources", []).extend(rule.get("sources", []))
    return rel
