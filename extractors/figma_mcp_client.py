import asyncio
import json
import os
import subprocess
from typing import Dict, Any, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class FigmaMCPClient:
    def __init__(self):
        self.figma_token = os.getenv("FIGMA_API_KEY") or os.getenv("FIGMA_ACCESS_TOKEN")
        self.session: Optional[ClientSession] = None
        self._client_context = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        if not self.figma_token:
            raise ValueError("FIGMA_API_KEY environment variable is required")
            
        # Configure MCP server parameters for Figma using the figma-developer-mcp package
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "figma-developer-mcp", f"--figma-api-key={self.figma_token}", "--stdio"]
        )
        
        # Create the stdio client context manager
        self._client_context = stdio_client(server_params)
        
        # Enter the context and get the streams
        read_stream, write_stream = await self._client_context.__aenter__()
        
        # Create and initialize the MCP client session
        self.session = ClientSession(read_stream, write_stream)
        await self.session.initialize()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if hasattr(self, '_client_context'):
            await self._client_context.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_file_structure(self, file_id: str) -> Dict[str, Any]:
        """Get the structure of a Figma file through MCP"""
        try:
            # List available tools first to see what's available
            tools = await self.session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools.tools]}")
            
            # Use the correct tool name: get_figma_data
            result = await self.session.call_tool(
                "get_figma_data",
                arguments={"fileKey": file_id}
            )
            
            if result.content and len(result.content) > 0:
                # Parse the JSON response
                content_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                file_data = json.loads(content_text)
                return file_data
            else:
                raise Exception("No content received from Figma MCP server")
                
        except Exception as e:
            print(f"Error getting Figma file structure: {e}")
            raise
    
    async def extract_components(self, file_id: str, component_pattern: str = "Entity") -> List[Dict[str, Any]]:
        """Extract components that match a pattern from Figma file"""
        try:
            # First get the file structure
            file_data = await self.get_file_structure(file_id)
            
            # Extract components from the file data
            components = []
            def traverse_nodes(node):
                if node.get("type") == "COMPONENT" and component_pattern.lower() in node.get("name", "").lower():
                    components.append(node)
                
                # Recursively traverse children
                for child in node.get("children", []):
                    traverse_nodes(child)
            
            # Start traversal from document root
            if "document" in file_data:
                for page in file_data["document"].get("children", []):
                    traverse_nodes(page)
            
            return components
                
        except Exception as e:
            print(f"Error extracting components from Figma: {e}")
            return []
    
    async def get_component_details(self, file_id: str, node_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific component"""
        try:
            # Use get_figma_data with specific nodeId to get component details
            result = await self.session.call_tool(
                "get_figma_data",
                arguments={
                    "fileKey": file_id,
                    "nodeId": node_id
                }
            )
            
            if result.content and len(result.content) > 0:
                content_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                node_data = json.loads(content_text)
                return node_data
            
            # Fallback: extract from file data
            file_data = await self.get_file_structure(file_id)
            return self._find_node_in_data(file_data, node_id)
                
        except Exception as e:
            print(f"Error getting component details: {e}")
            return {}
    
    def _find_node_in_data(self, data: Dict[str, Any], node_id: str) -> Dict[str, Any]:
        """Helper method to find a specific node in the file data"""
        def search_node(node):
            if node.get("id") == node_id:
                return node
            
            for child in node.get("children", []):
                result = search_node(child)
                if result:
                    return result
            return None
        
        if "document" in data:
            for page in data["document"].get("children", []):
                result = search_node(page)
                if result:
                    return result
        
        return {}

async def extract_figma_entities_via_mcp(file_id: str) -> Dict[str, Any]:
    """Extract entities from Figma using MCP"""
    print(f"🎨 [FIGMA] Starting entity extraction from file: {file_id}")
    
    async with FigmaMCPClient() as figma_client:
        print(f"🎨 [FIGMA] MCP client connected, getting file structure...")
        # Get file structure
        file_data = await figma_client.get_file_structure(file_id)
        print(f"🎨 [FIGMA] File structure obtained")
        
        print(f"🎨 [FIGMA] Extracting entity components...")
        # Extract entity components
        entity_components = await figma_client.extract_components(file_id, "Entity")
        print(f"🎨 [FIGMA] Found {len(entity_components)} entity components")
        
        # Process components into entity cards
        entity_cards = []
        connectors = []
        
        for component in entity_components:
            node_id = component.get("id")
            if node_id:
                # Get detailed component information
                details = await figma_client.get_component_details(file_id, node_id)
                
                # Extract entity information
                entity_card = {
                    "name": component.get("name", "Unknown").replace("Entity:", "").strip(),
                    "attributes": extract_attributes_from_component(details),
                    "sources": [f"figma:node:{node_id}"]
                }
                entity_cards.append(entity_card)
        
        # Extract connectors/relationships (if they exist as separate components)
        relationship_components = await figma_client.extract_components(file_id, "Relationship")
        
        for rel_component in relationship_components:
            connector = {
                "from": extract_source_entity(rel_component),
                "to": extract_target_entity(rel_component),
                "label": rel_component.get("name", "1:N"),
                "sources": [f"figma:edge:{rel_component.get('id')}"]
            }
            connectors.append(connector)
        
        return {
            "figma": {
                "entityCards": entity_cards,
                "connectors": connectors,
                "sources": [f"figma:file:{file_id}"]
            }
        }

def extract_attributes_from_component(component_details: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract attributes from component details"""
    attributes = []
    
    # Look for text layers that might represent attributes
    def traverse_for_attributes(node):
        if node.get("type") == "TEXT":
            text = node.get("characters", "")
            # Parse attribute definitions (e.g., "id: UUID (PK)")
            if ":" in text:
                attr_name = text.split(":")[0].strip()
                attr_info = text.split(":")[1].strip() if len(text.split(":")) > 1 else ""
                
                # Detect tags from attribute info
                tags = []
                if "(PK)" in attr_info.upper() or "PRIMARY" in attr_info.upper():
                    tags.append("pk")
                if "UNIQUE" in attr_info.upper():
                    tags.append("unique")
                
                attributes.append({
                    "name": attr_name,
                    "tags": tags
                })
        
        # Recursively check children
        for child in node.get("children", []):
            traverse_for_attributes(child)
    
    traverse_for_attributes(component_details)
    return attributes

def extract_source_entity(relationship_component: Dict[str, Any]) -> str:
    """Extract source entity from relationship component"""
    # This would depend on your Figma naming convention
    name = relationship_component.get("name", "")
    if " to " in name:
        return name.split(" to ")[0].strip()
    return "Unknown"

def extract_target_entity(relationship_component: Dict[str, Any]) -> str:
    """Extract target entity from relationship component"""
    # This would depend on your Figma naming convention
    name = relationship_component.get("name", "")
    if " to " in name:
        return name.split(" to ")[1].strip()
    return "Unknown"

# Synchronous wrapper for use in the main pipeline
def create_context_pack_from_figma_mcp(file_id: str) -> Dict[str, Any]:
    """Synchronous wrapper for creating context pack from Figma via MCP"""
    print(f"🎨 [FIGMA] Starting synchronous wrapper for file: {file_id}")
    result = asyncio.run(extract_figma_entities_via_mcp(file_id))
    print(f"🎨 [FIGMA] Synchronous wrapper completed")
    return result