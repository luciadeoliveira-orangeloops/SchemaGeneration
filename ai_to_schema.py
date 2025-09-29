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

def convert_ai_analysis_to_context_pack(ai_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Convert AI analysis format to context-pack format"""
    
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
    
    # Create context pack
    context_pack = {
        "figma": {
            "entityCards": entity_cards,
            "connectors": connectors,
            "sources": ["figma:ai_analysis"]
        },
        "documents": {
            "glossary": [],
            "rules": [],
            "enums": []
        },
        "meta": {
            "source": "figma_ai_analysis",
            "generated_at": datetime.now().isoformat() + "Z",
            "entities_count": len(entity_cards),
            "relationships_count": len(connectors)
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
    """Generate complete schema from Figma using AI analysis"""
    
    print("🚀 Starting AI-powered Figma-to-Schema generation...")
    
    # Step 1: Check if we have AI analysis, if not create it
    ai_analysis_path = "context/figma-ai-analysis.json"
    
    if not os.path.exists(ai_analysis_path):
        print("\n📋 Step 1: Creating AI analysis...")
        analyzer = FigmaAIAnalyzer()
        
        try:
            # Load raw Figma data
            with open("context/figma-mcp-raw-response.json", "r") as f:
                figma_data = json.load(f)
            
            # Analyze with AI
            ai_analysis = analyzer.analyze_figma_data(figma_data)
            
            # Save analysis
            with open(ai_analysis_path, "w", encoding="utf-8") as f:
                json.dump(ai_analysis, f, indent=2, ensure_ascii=False)
            
            print(f"✅ AI Analysis created:")
            print(f"   • Entities: {len(ai_analysis.get('entities', []))}")
            print(f"   • Relationships: {len(ai_analysis.get('relationships', []))}")
            
        except FileNotFoundError:
            print("❌ No Figma data found. Run simple_figma_test.py first.")
            return
        except Exception as e:
            print(f"❌ Error in AI analysis: {e}")
            return
    else:
        print("\n📋 Step 1: Loading existing AI analysis...")
        with open(ai_analysis_path, "r") as f:
            ai_analysis = json.load(f)
        
        print(f"✅ AI Analysis loaded:")
        print(f"   • Entities: {len(ai_analysis.get('entities', []))}")
        print(f"   • Relationships: {len(ai_analysis.get('relationships', []))}")
    
    # Step 2: Convert AI analysis to context pack format
    print("\n📦 Step 2: Converting to context pack format...")
    
    context_pack = convert_ai_analysis_to_context_pack(ai_analysis)
    
    # Save context pack
    context_pack_path = "context/context-pack.json"
    with open(context_pack_path, "w", encoding="utf-8") as f:
        json.dump(context_pack, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Context pack created:")
    print(f"   • Entity cards: {len(context_pack['figma']['entityCards'])}")
    print(f"   • Connectors: {len(context_pack['figma']['connectors'])}")
    
    # Step 3: Run complete pipeline
    print("\n⚙️ Step 3: Running complete schema generation pipeline...")
    
    try:
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