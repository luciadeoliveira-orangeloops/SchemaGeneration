#!/usr/bin/env python3
"""
Convert AI analysis to context pack format and run complete pipeline
"""
import json
import os
import sys
import subprocess
from datetime import datetime
from typing import Dict, Any

from extractors.figma_ai_analyzer import FigmaAIAnalyzer
from extractors.docs_mcp import DocumentsMCPClient
from simple_figma_test import create_context_pack_from_figma_simple

def convert_ai_analysis_to_context_pack(ai_analysis: Dict[str, Any], docs_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convert AI analysis format to context-pack format, optionally including documents context"""
    
    entity_cards = []
    connectors = []
    
    # Convert entities
    for entity in ai_analysis.get("entities", []):
        entity_card = {
            "name": entity["name"],
            "attributes": [],
            "sources": entity.get("sources", [])
        }
        
        # Convert attributes
        for attr in entity.get("attributes", []):
            attr_obj = {
                "name": attr["name"],
                "tags": attr.get("tags", [])
            }
            entity_card["attributes"].append(attr_obj)
        
        entity_cards.append(entity_card)
    
    # Convert relationships to connectors
    for rel in ai_analysis.get("relationships", []):
        connector = {
            "from": rel["from_entity"],
            "to": rel["to_entity"],
            "label": _convert_relationship_type_to_label(rel["relationship_type"]),
            "sources": [f"ai_analysis:{rel['from_entity']}-{rel['to_entity']}"]
        }
        connectors.append(connector)
    
    # Add connectors from documents if available
    if docs_context:
        for rule in docs_context.get("rules", []):
            if rule.get("kind") == "cardinality" and rule.get("from") and rule.get("to"):
                connector = {
                    "from": rule["from"],
                    "to": rule["to"],
                    "label": _convert_relationship_type_to_label(rule.get("type", "many-to-one")),
                    "sources": rule.get("sources", ["docs:business_rules"])
                }
                connectors.append(connector)
    
    # Create context pack
    context_pack = {
        "figma": {
            "entityCards": entity_cards,
            "connectors": connectors,
            "sources": ["figma:ai_analysis"]
        },
        "documents": docs_context or {
            "glossary": [],
            "rules": [],
            "enums": []
        },
        "meta": {
            "source": "figma_ai_analysis_with_docs",
            "generated_at": datetime.now().isoformat() + "Z",
            "entities_count": len(entity_cards),
            "relationships_count": len(connectors),
            "docs_terms": len((docs_context or {}).get("glossary", [])),
            "docs_rules": len((docs_context or {}).get("rules", [])),
            "docs_enums": len((docs_context or {}).get("enums", []))
        }
    }
    
    return context_pack

def _convert_relationship_type_to_label(rel_type: str) -> str:
    """Convert relationship type to connector label"""
    mapping = {
        "one_to_one": "1:1",
        "one_to_many": "1:N",
        "many_to_one": "N:1", 
        "many_to_many": "N:N"
    }
    return mapping.get(rel_type, "1:N")

def main():
    """Generate complete schema from Figma using AI analysis and documentation"""
    
    print("🚀 Starting AI-powered Figma + Docs to Schema generation...")
    
    # Step 1: Extract documentation context
    print("\n📚 Step 1: Extracting documentation context...")
    docs_dir = os.getenv("DOCS_RESOURCES_DIR", "./docs")
    docs_client = DocumentsMCPClient(docs_dir)
    docs_context = docs_client.extract_documents_context()
    
    print(f"✅ Documentation context extracted:")
    print(f"   • Glossary terms: {len(docs_context['glossary'])}")
    print(f"   • Business rules: {len(docs_context['rules'])}")  
    print(f"   • Enums: {len(docs_context['enums'])}")
    
    # Step 2: Extract Figma data and create AI analysis
    print("\n🎨 Step 2: Extracting and analyzing Figma data...")
    ai_analysis_path = "context/figma-ai-analysis.json"
    
    try:
        # Get Figma file ID from environment
        figma_file_id = os.getenv("FIGMA_FILE_ID")
        if not figma_file_id:
            print("❌ FIGMA_FILE_ID not set in environment variables")
            return
        
        print(f"🔍 Extracting data from Figma file: {figma_file_id}")
        
        # Extract raw Figma data via MCP
        figma_raw_data = create_context_pack_from_figma_simple(figma_file_id)
        
        # Save raw data for debugging
        os.makedirs("context", exist_ok=True)
        with open("context/figma-mcp-raw-response.json", "w", encoding="utf-8") as f:
            json.dump(figma_raw_data, f, indent=2, ensure_ascii=False)
        
        print("✅ Figma data extracted successfully")
        
        # Create AI analyzer and analyze the data
        print("🤖 Analyzing Figma data with OpenAI...")
        analyzer = FigmaAIAnalyzer()
        ai_analysis = analyzer.analyze_figma_data(figma_raw_data)
        
        # Save AI analysis
        with open(ai_analysis_path, "w", encoding="utf-8") as f:
            json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
        
        print(f"✅ AI Analysis completed:")
        print(f"   • Entities: {len(ai_analysis.get('entities', []))}")
        print(f"   • Relationships: {len(ai_analysis.get('relationships', []))}")
        
    except Exception as e:
        print(f"❌ Error in Figma extraction/analysis: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Convert to context pack format with documentation
    print("\n📦 Step 3: Merging Figma + Documentation into context pack...")
    
    context_pack = convert_ai_analysis_to_context_pack(ai_analysis, docs_context)
    
    # Save context pack
    context_pack_path = "context/context-pack.json"
    with open(context_pack_path, "w", encoding="utf-8") as f:
        json.dump(context_pack, f, indent=2, ensure_ascii=False)
    print(f"✅ Context pack created:")
    print(f"   • Entity cards: {len(context_pack['figma']['entityCards'])}")
    print(f"   • Connectors: {len(context_pack['figma']['connectors'])}")
    print(f"   • Documentation terms: {len(context_pack['documents']['glossary'])}")
    print(f"   • Documentation rules: {len(context_pack['documents']['rules'])}")
    print(f"   • Documentation enums: {len(context_pack['documents']['enums'])}")
    
    # Step 4: Run complete pipeline
    print("\n⚙️ Step 4: Running complete schema generation pipeline...")
    
    try:
        # Ensure schema directory exists
        os.makedirs("schema", exist_ok=True)
        
        # Run pipeline using subprocess
        result = subprocess.run([
            "python", "-m", "pipeline.run_all", "mer", 
            context_pack_path, "schema/mer.json"
        ], capture_output=True, text=True, check=True)
        
        print("✅ Pipeline output:")
        if result.stdout:
            print(result.stdout)
        
        # Load the generated schema
        with open("schema/mer.json", "r") as f:
            final_schema = json.load(f)
        
        print("\n🎉 SUCCESS! Schema generation complete!")
        print(f"📄 Final schema saved to: schema/mer.json")
        
        # Show summary
        entities = final_schema.get("entities", [])
        relationships = final_schema.get("relationships", [])
        
        print(f"\n📊 FINAL SCHEMA SUMMARY:")
        print(f"   📋 Total entities: {len(entities)}")
        print(f"   🔗 Total relationships: {len(relationships)}")
        
        for entity in entities:
            name = entity.get("name", "Unknown")
            attrs = len(entity.get("attributes", []))
            print(f"   • {name}: {attrs} attributes")
        
        for rel in relationships:
            from_e = rel.get("from_entity", "?")
            to_e = rel.get("to_entity", "?")
            rel_type = rel.get("relationship_type", "unknown")
            print(f"   • {from_e} -> {to_e} ({rel_type})")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Pipeline error (exit code {e.returncode}):")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return
    except Exception as e:
        print(f"❌ Error in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"\n✨ All done! You can now use the schema for:")
    print(f"   • Generate Prisma schema: uv run projectors/prisma/to_prisma.py")
    print(f"   • View schema: cat schema/mer.json")

if __name__ == "__main__":
    main()