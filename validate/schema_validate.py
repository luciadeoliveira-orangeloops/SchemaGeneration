from typing import Dict, Any

def validate_mer_basic(mer: Dict[str, Any]) -> None:
    assert isinstance(mer, dict), "MER must be a dictionary"
    assert "entities" in mer and isinstance(mer["entities"], list), "MER.entities must be a list"
    assert "relationships" in mer and isinstance(mer["relationships"], list), "MER.relationships must be a list"
    # pk present
    for e in mer["entities"]:
        attrs = e.get("attributes", [])
        assert any(a.get("pk") for a in attrs), f"The entity {e.get('name')} does not have a primary key (pk)"
