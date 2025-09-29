#!/usr/bin/env python3
"""
Simplified Figma MCP client using subprocess
"""
import json
import os
import subprocess
import sys
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def call_figma_mcp(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call Figma MCP tool using subprocess"""
    figma_api_key = os.getenv("FIGMA_API_KEY") or os.getenv("FIGMA_ACCESS_TOKEN")
    
    if not figma_api_key:
        raise ValueError("FIGMA_API_KEY environment variable is required")
    
    try:
        # Call the figma-developer-mcp via npx
        cmd = [
            "npx", "-y", "figma-developer-mcp", 
            f"--figma-api-key={figma_api_key}", 
            "--stdio"
        ]
        
        print(f"🔧 Calling MCP tool: {tool_name}")
        print(f"📋 Arguments: {arguments}")
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0
        )
        
        # MCP Protocol requires initialization first
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "figma-schema-generator", "version": "1.0.0"}
            }
        }
        
        print("🔄 Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read initialize response
        init_response_line = process.stdout.readline()
        if init_response_line:
            print(f"📨 Init response: {init_response_line.strip()}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        print("🔄 Sending initialized notification...")
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        
        # Now send the actual tool call
        tool_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        print("🔄 Sending tool call request...")
        process.stdin.write(json.dumps(tool_request) + "\n")
        process.stdin.flush()
        
        # Read tool response
        tool_response_line = process.stdout.readline()
        
        if not tool_response_line:
            stderr_content = process.stderr.read()
            print(f"❌ No response received. STDERR: {stderr_content}")
            raise Exception(f"No response from MCP server. STDERR: {stderr_content}")
        
        print(f"📨 Tool response: {tool_response_line.strip()}")
        
        # Parse the response
        try:
            response = json.loads(tool_response_line)
            
            if "error" in response:
                raise Exception(f"MCP error: {response['error']}")
            
            return response.get("result", {})
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse MCP response: {e}")
            print(f"Raw response: {tool_response_line}")
            raise Exception(f"Invalid JSON response from MCP: {tool_response_line}")
        
        finally:
            process.terminate()
            process.wait()
    
    except Exception as e:
        raise Exception(f"Error calling Figma MCP: {e}")

def get_figma_file_data(file_id: str) -> Dict[str, Any]:
    """Get Figma file data using MCP"""
    return call_figma_mcp("get_figma_data", {"fileKey": file_id})

def extract_entities_from_figma_data(file_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract entity-like components from Figma data"""
    entities = []
    
    def traverse_nodes(node, path=""):
        node_name = node.get("name", "")
        node_type = node.get("type", "")
        
        # Look for components that might represent entities
        if (node_type == "COMPONENT" and 
            ("entity" in node_name.lower() or 
             "model" in node_name.lower() or
             "table" in node_name.lower())):
            
            entity = {
                "name": clean_entity_name(node_name),
                "attributes": extract_attributes_from_node(node),
                "sources": [f"figma:node:{node.get('id')}"],
                "raw_name": node_name,
                "path": path
            }
            entities.append(entity)
            print(f"📋 Found entity: {entity['name']} ({node_name})")
        
        # Also look for text nodes that might contain entity definitions
        elif node_type == "TEXT":
            text_content = node.get("characters", "")
            if is_entity_definition(text_content):
                entity = parse_entity_from_text(text_content, node.get('id'))
                if entity:
                    entities.append(entity)
                    print(f"📝 Found text entity: {entity['name']}")
        
        # Recursively traverse children
        for child in node.get("children", []):
            traverse_nodes(child, f"{path}/{node_name}" if path else node_name)
    
    # Start traversal
    document = file_data.get("document", {})
    for page in document.get("children", []):
        traverse_nodes(page)
    
    return entities

def clean_entity_name(name: str) -> str:
    """Clean entity name"""
    # Remove common prefixes/suffixes
    name = name.replace("Entity:", "").replace("Model:", "").replace("Table:", "")
    name = name.strip()
    
    # Convert to PascalCase
    words = name.replace("-", " ").replace("_", " ").split()
    return "".join(word.capitalize() for word in words if word)

def extract_attributes_from_node(node: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract attributes from a node"""
    attributes = []
    
    def find_text_attributes(n):
        if n.get("type") == "TEXT":
            text = n.get("characters", "")
            attrs = parse_attributes_from_text(text)
            attributes.extend(attrs)
        
        for child in n.get("children", []):
            find_text_attributes(child)
    
    find_text_attributes(node)
    return attributes

def parse_attributes_from_text(text: str) -> List[Dict[str, Any]]:
    """Parse attributes from text content"""
    attributes = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for patterns like "id: UUID (PK)" or "email: string"
        if ':' in line:
            parts = line.split(':', 1)
            attr_name = parts[0].strip()
            attr_info = parts[1].strip() if len(parts) > 1 else ""
            
            # Skip if it looks like a title or section header
            if len(attr_name.split()) > 3:
                continue
            
            tags = []
            if '(PK)' in attr_info.upper() or 'PRIMARY' in attr_info.upper():
                tags.append("pk")
            if 'UNIQUE' in attr_info.upper():
                tags.append("unique")
            if 'NOT NULL' in attr_info.upper() or 'REQUIRED' in attr_info.upper():
                tags.append("required")
            
            attributes.append({
                "name": attr_name,
                "tags": tags,
                "raw_info": attr_info
            })
    
    return attributes

def is_entity_definition(text: str) -> bool:
    """Check if text looks like an entity definition"""
    # Simple heuristics
    lines = text.split('\n')
    colon_lines = [line for line in lines if ':' in line]
    
    # If more than 2 lines have colons, might be an entity definition
    return len(colon_lines) >= 2

def parse_entity_from_text(text: str, node_id: str) -> Dict[str, Any]:
    """Parse entity from text content"""
    lines = text.split('\n')
    if not lines:
        return None
    
    # First line might be the entity name
    entity_name = lines[0].strip()
    
    # Rest are attributes
    attributes = []
    for line in lines[1:]:
        line = line.strip()
        if ':' in line:
            parts = line.split(':', 1)
            attr_name = parts[0].strip()
            attr_info = parts[1].strip() if len(parts) > 1 else ""
            
            tags = []
            if '(PK)' in attr_info.upper():
                tags.append("pk")
            if 'UNIQUE' in attr_info.upper():
                tags.append("unique")
            
            attributes.append({
                "name": attr_name,
                "tags": tags,
                "raw_info": attr_info
            })
    
    if not attributes:
        return None
    
    return {
        "name": clean_entity_name(entity_name),
        "attributes": attributes,
        "sources": [f"figma:text:{node_id}"],
        "raw_name": entity_name
    }

def create_context_pack_from_figma_simple(file_id: str) -> Dict[str, Any]:
    """Create context pack from Figma using simplified MCP approach"""
    print(f"🎨 Extracting data from Figma file: {file_id}")
    
    # Get file data from Figma MCP
    file_data = get_figma_file_data(file_id)
    
    # Save COMPLETE raw Figma data for debugging and analysis
    raw_output_path = "context/figma-mcp-raw-response.json"
    os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)
    
    with open(raw_output_path, "w", encoding="utf-8") as f:
        json.dump(file_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Complete MCP response saved to: {raw_output_path}")
    print(f"🔍 Data contains {len(file_data)} top-level keys")
    
    # Also extract just text and component information for easier analysis
    simplified_data = extract_simplified_figma_data(file_data)
    
    # Save simplified version for OpenAI analysis
    simplified_output_path = "context/figma-simplified-for-ai.json"
    with open(simplified_output_path, "w", encoding="utf-8") as f:
        json.dump(simplified_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Simplified data for AI saved to: {simplified_output_path}")
    
    # For now, return raw data structure - we'll let OpenAI analyze this
    return {
        "figma": {
            "raw_data": file_data,
            "simplified_data": simplified_data,
            "entityCards": [],  # Will be populated by OpenAI analysis
            "connectors": [],   # Will be populated by OpenAI analysis
            "sources": [f"figma:file:{file_id}"]
        }
    }

def extract_simplified_figma_data(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract key information from Figma data for AI analysis"""
    simplified = {
        "components": [],
        "text_elements": [],
        "pages": [],
        "metadata": {}
    }
    
    # Extract basic file info
    if "name" in file_data:
        simplified["metadata"]["file_name"] = file_data["name"]
    if "lastModified" in file_data:
        simplified["metadata"]["last_modified"] = file_data["lastModified"]
    
    def traverse_node(node, parent_name=""):
        node_name = node.get("name", "")
        node_type = node.get("type", "")
        node_id = node.get("id", "")
        
        full_path = f"{parent_name}/{node_name}" if parent_name else node_name
        
        # Collect components (could be UI components representing entities)
        if node_type == "COMPONENT":
            simplified["components"].append({
                "id": node_id,
                "name": node_name,
                "path": full_path,
                "type": node_type
            })
        
        # Collect text elements (could contain entity names, field names, etc.)
        elif node_type == "TEXT":
            text_content = node.get("characters", "")
            if text_content.strip():  # Only non-empty text
                simplified["text_elements"].append({
                    "id": node_id,
                    "text": text_content,
                    "path": full_path,
                    "parent": parent_name
                })
        
        # Collect page information
        elif node_type == "CANVAS":  # Figma pages are CANVAS type
            simplified["pages"].append({
                "id": node_id,
                "name": node_name,
                "child_count": len(node.get("children", []))
            })
        
        # Recursively process children
        for child in node.get("children", []):
            traverse_node(child, full_path)
    
    # Start traversal from document
    document = file_data.get("document", {})
    traverse_node(document)
    
    return simplified

def main():
    """Test the simplified Figma MCP client"""
    file_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv("FIGMA_FILE_ID")
    
    if not file_id:
        print("Usage: python simple_figma_test.py <file_id>")
        print("Or set FIGMA_FILE_ID environment variable")
        sys.exit(1)
    
    try:
        context_pack = create_context_pack_from_figma_simple(file_id)
        
        # Save to file
        output_path = "context/figma-simple-test.json"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(context_pack, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Context pack saved to: {output_path}")
        
        # Show summary
        entities = context_pack["figma"]["entityCards"]
        for entity in entities:
            print(f"📋 Entity: {entity['name']} ({len(entity['attributes'])} attributes)")
            for attr in entity['attributes'][:3]:  # Show first 3 attributes
                tags_str = f" [{', '.join(attr['tags'])}]" if attr['tags'] else ""
                print(f"   - {attr['name']}{tags_str}")
            if len(entity['attributes']) > 3:
                print(f"   ... and {len(entity['attributes']) - 3} more")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()