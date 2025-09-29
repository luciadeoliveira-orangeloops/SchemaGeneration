from typing import Dict, Any, List

def extract_figma_candidates(context_pack: Dict[str, Any]) -> Dict[str, Any]:
    """Returns candidates for entities/attributes/relationships from the 'figma' section of the context pack.
    Assumes the context pack includes an optional section:
    {
      "figma": {
        "entityCards": [
          {"name":"User","attributes":[{"name":"id","tags":["pk"]},{"name":"email","tags":["unique"]}], "sources":["figma:node123"] }
        ],
        "connectors": [
          {"from":"Order","to":"User","label":"1:N","sources":["figma:edge42"]}
        ]
      }
    }
    """
    figma = context_pack.get("figma", {})
    return {
        "entities": figma.get("entityCards", []),
        "connectors": figma.get("connectors", []),
        "sources": figma.get("sources", [])
    }
