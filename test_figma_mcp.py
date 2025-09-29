#!/usr/bin/env python3
"""
Test script to verify Figma MCP connection
"""
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from extractors.figma_mcp_client import FigmaMCPClient

async def test_figma_connection(file_id: str):
    """Test the Figma MCP connection"""
    print(f"🧪 Testing Figma MCP connection with file ID: {file_id}")
    
    try:
        async with FigmaMCPClient() as figma_client:
            print("✅ Successfully connected to Figma MCP server")
            
            # List available tools
            tools = await figma_client.session.list_tools()
            print(f"📋 Available tools: {[tool.name for tool in tools.tools]}")
            
            # Try to get file structure
            print("🔍 Getting file structure...")
            file_data = await figma_client.get_file_structure(file_id)
            
            if file_data:
                print(f"✅ Successfully retrieved file data")
                print(f"📄 File name: {file_data.get('name', 'Unknown')}")
                
                # Count pages and components
                pages = file_data.get('document', {}).get('children', [])
                print(f"📑 Pages found: {len(pages)}")
                
                # Look for entity components
                entity_components = await figma_client.extract_components(file_id, "Entity")
                print(f"🏗️  Entity components found: {len(entity_components)}")
                
                for component in entity_components[:3]:  # Show first 3
                    print(f"   - {component.get('name', 'Unnamed')}")
            else:
                print("❌ No file data received")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_figma_mcp.py <figma_file_id>")
        print("Or set FIGMA_FILE_ID environment variable")
        sys.exit(1)
    
    file_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv("FIGMA_FILE_ID")
    
    if not file_id:
        print("❌ Error: Figma file ID is required")
        sys.exit(1)
    
    if not (os.getenv("FIGMA_API_KEY") or os.getenv("FIGMA_ACCESS_TOKEN")):
        print("❌ Error: FIGMA_API_KEY environment variable is required")
        sys.exit(1)
    
    success = asyncio.run(test_figma_connection(file_id))
    
    if success:
        print("🎉 Figma MCP connection test successful!")
    else:
        print("💥 Figma MCP connection test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()