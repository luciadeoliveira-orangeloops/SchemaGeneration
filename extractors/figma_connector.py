import os
import requests
from typing import Dict, Any, List

class FigmaConnector:
    def __init__(self):
        self.access_token = os.getenv("FIGMA_ACCESS_TOKEN")
        self.base_url = "https://api.figma.com/v1"
        
    def get_file_data(self, file_id: str) -> Dict[str, Any]:
        """Fetch file data from Figma API"""
        if not self.access_token:
            raise ValueError("FIGMA_ACCESS_TOKEN environment variable is required")
            
        headers = {
            "X-Figma-Token": self.access_token
        }
        
        response = requests.get(f"{self.base_url}/files/{file_id}", headers=headers)
        response.raise_for_status()
        return response.json()
    
    def extract_entity_cards(self, file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract entity-like components from Figma file"""
        entities = []
        
        def traverse_nodes(node, parent_id=""):
            if node.get("type") == "COMPONENT" and "entity" in node.get("name", "").lower():
                # Extract entity information from component
                entity = {
                    "name": node.get("name", "").replace("Entity:", "").strip(),
                    "attributes": self._extract_attributes_from_node(node),
                    "sources": [f"figma:node:{node.get('id')}"]
                }
                entities.append(entity)
            
            # Recursively traverse children
            for child in node.get("children", []):
                traverse_nodes(child, node.get("id"))
        
        # Start traversal from document root
        for page in file_data.get("document", {}).get("children", []):
            traverse_nodes(page)
            
        return entities
    
    def _extract_attributes_from_node(self, node: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract attributes from entity node (simplified implementation)"""
        attributes = []
        
        # Look for text nodes that might represent attributes
        def find_text_nodes(n):
            if n.get("type") == "TEXT":
                text = n.get("characters", "")
                if ":" in text:  # Likely an attribute definition
                    attr_name = text.split(":")[0].strip()
                    attributes.append({
                        "name": attr_name,
                        "tags": ["inferred"]  # You could add logic to detect pk, unique, etc.
                    })
            
            for child in n.get("children", []):
                find_text_nodes(child)
        
        find_text_nodes(node)
        return attributes
    
    def extract_connectors(self, file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract relationship connectors from Figma file"""
        connectors = []
        
        # Implementation would depend on how relationships are represented in your Figma file
        # This is a simplified version
        
        return connectors

def create_context_pack_from_figma(file_id: str) -> Dict[str, Any]:
    """Create a context pack from Figma file"""
    connector = FigmaConnector()
    file_data = connector.get_file_data(file_id)
    
    entity_cards = connector.extract_entity_cards(file_data)
    connectors = connector.extract_connectors(file_data)
    
    return {
        "figma": {
            "entityCards": entity_cards,
            "connectors": connectors,
            "sources": [f"figma:file:{file_id}"]
        },
        "documents": {
            "glossary": [],
            "rules": [],
            "enums": []
        }
    }