from typing import Dict, Any, List

def extract_doc_facts(context_pack: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts definitions and rules from the 'documents' section of the context pack.
    Suggested structure:
    {
      "documents": {
        "glossary": [{"term":"User","definition":"...","aliases":["Customer"]}],
        "rules": [{"kind":"cardinality","from":"Order","to":"User","type":"many-to-one","sources":["doc:spec#4.2"]}],
        "enums": [{"name":"OrderStatus","values":["pending","paid","shipped","cancelled"],"sources":["doc:api#status"]}]
      }
    }
    """
    docs = context_pack.get("documents", {})
    return {
        "glossary": docs.get("glossary", []),
        "rules": docs.get("rules", []),
        "enums": docs.get("enums", []),
        "sources": docs.get("sources", [])
    }
