#!/usr/bin/env python3
"""
Script to generate a context pack from Figma using MCP and run the full pipeline
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import List

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from simple_figma_test import create_context_pack_from_figma_simple
from pipeline.run_all import load_context, merge_parts
from pipeline.passes.entities import run_entities
from pipeline.passes.atributes import run_attributes
from pipeline.passes.relationships import run_relationships
from pipeline.passes.emit import write_mer
from merge.align import unify_naming
from merge.rules import resolve_cardinality
from validate.schema_validate import validate_mer_basic
from llm.openai_client import run_model

def ensure_directories():
    """Ensure output directories exist"""
    Path("context").mkdir(exist_ok=True)
    Path("schema").mkdir(exist_ok=True)

def generate_context_pack_from_figma(file_id: str, output_path: str):
    """Generate context pack from Figma file"""
    print(f"🎨 Extracting data from Figma file: {file_id}")
    
    try:
        # Extract data from Figma via MCP
        figma_data = create_context_pack_from_figma_simple(file_id)
        
        # Create a complete context pack
        context_pack = {
            **figma_data,
            "documents": {
                "glossary": [],
                "rules": [],
                "enums": []
            },
            "meta": {
                "source": "figma_mcp",
                "file_id": file_id,
                "generated_at": None
            }
        }
        
        # Save context pack
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(context_pack, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Context pack saved to: {output_path}")
        return context_pack
        
    except Exception as e:
        print(f"❌ Error generating context pack from Figma: {e}")
        raise

def generate_context_pack_from_multiple_figma_files(file_ids: List[str], output_path: str):
    """Generate context pack from multiple Figma files"""
    print(f"🎨 Extracting data from {len(file_ids)} Figma files")
    
    all_entity_cards = []
    all_connectors = []
    all_sources = []
    
    try:
        for i, file_id in enumerate(file_ids, 1):
            print(f"🔄 Processing file {i}/{len(file_ids)}: {file_id}")
            
            # Extract data from each Figma file
            figma_data = create_context_pack_from_figma_simple(file_id)
            
            # Merge data from all files
            figma_section = figma_data.get("figma", {})
            all_entity_cards.extend(figma_section.get("entityCards", []))
            all_connectors.extend(figma_section.get("connectors", []))
            all_sources.extend(figma_section.get("sources", []))
        
        # Create combined context pack
        context_pack = {
            "figma": {
                "entityCards": all_entity_cards,
                "connectors": all_connectors,
                "sources": all_sources
            },
            "documents": {
                "glossary": [],
                "rules": [],
                "enums": []
            },
            "meta": {
                "source": "figma_mcp_multiple",
                "file_ids": file_ids,
                "generated_at": None,
                "total_files": len(file_ids),
                "total_entities": len(all_entity_cards),
                "total_connectors": len(all_connectors)
            }
        }
        
        # Save combined context pack
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(context_pack, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Combined context pack saved to: {output_path}")
        print(f"📊 Total entities: {len(all_entity_cards)}, connectors: {len(all_connectors)}")
        return context_pack
        
    except Exception as e:
        print(f"❌ Error generating context pack from multiple Figma files: {e}")
        raise

def run_full_pipeline(context_pack_path: str, mer_output_path: str):
    """Run the full MER generation pipeline"""
    print(f"🔄 [PIPELINE] Starting MER generation pipeline...")
    
    # Load context pack
    print(f"📖 [PIPELINE] Loading context pack from: {context_pack_path}")
    ctx = load_context(context_pack_path)
    print(f"📖 [PIPELINE] Context pack loaded successfully")
    
    # Run LLM passes
    print("🚀 [PIPELINE] Starting entities pass...")
    e = run_entities(ctx, run_model)
    print(f"✅ [PIPELINE] Entities pass completed - found {len(e.get('entities', []))} entities")
    
    print("🚀 [PIPELINE] Starting attributes pass...")
    a = run_attributes(ctx, e, run_model)
    print(f"✅ [PIPELINE] Attributes pass completed")
    
    print("🚀 [PIPELINE] Starting relationships pass...")
    r = run_relationships(ctx, a, run_model)
    print(f"✅ [PIPELINE] Relationships pass completed - found {len(r.get('relationships', []))} relationships")
    
    # Merge results
    print("🔀 [PIPELINE] Merging results...")
    mer = merge_parts(e, a, r, ctx)
    mer = unify_naming(mer, (ctx.get("documents") or {}).get("glossary", []))
    print("🔀 [PIPELINE] Results merged successfully")
    
    # Validate
    print("✅ [PIPELINE] Validating MER...")
    validate_mer_basic(mer)
    print("✅ [PIPELINE] MER validation passed")
    
    # Save MER
    print(f"💾 [PIPELINE] Saving MER to: {mer_output_path}")
    write_mer(mer, mer_output_path)
    print(f"✅ [PIPELINE] MER generated successfully: {mer_output_path}")
    
    return mer

def main():
    parser = argparse.ArgumentParser(description="Generate schema from Figma using MCP")
    
    parser.add_argument("--figma-file-ids", 
                       nargs='+',
                       help="Multiple Figma file IDs (space separated)")
    parser.add_argument("--figma-file-id", 
                       help="Single Figma file ID (can also use FIGMA_FILE_ID env var)")
    parser.add_argument("--context-output", 
                       default="context/context-pack.json",
                       help="Output path for context pack")
    parser.add_argument("--mer-output", 
                       default="schema/mer.json",
                       help="Output path for MER JSON")
    parser.add_argument("--skip-figma", 
                       action="store_true",
                       help="Skip Figma extraction and use existing context pack")
    
    args = parser.parse_args()
    
    # Get Figma file IDs
    figma_file_ids = []
    if args.figma_file_ids:
        figma_file_ids = args.figma_file_ids
    elif args.figma_file_id:
        figma_file_ids = [args.figma_file_id]
    elif os.getenv("FIGMA_FILE_ID"):
        figma_file_ids = [os.getenv("FIGMA_FILE_ID")]
    elif os.getenv("FIGMA_FILE_IDS"):
        # Support comma-separated list in env var
        figma_file_ids = [id.strip() for id in os.getenv("FIGMA_FILE_IDS").split(",")]
    
    if not args.skip_figma and not figma_file_ids:
        print("❌ Error: Figma file ID(s) required. Use --figma-file-ids, --figma-file-id, or set FIGMA_FILE_ID env var")
        sys.exit(1)
    
    # Check OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        sys.exit(1)
    
    ensure_directories()
    
    try:
        # Generate context pack from Figma if not skipping
        if not args.skip_figma:
            generate_context_pack_from_multiple_figma_files(figma_file_ids, args.context_output)
        else:
            print(f"⏭️  Skipping Figma extraction, using existing: {args.context_output}")
        
        # Run the full pipeline
        mer = run_full_pipeline(args.context_output, args.mer_output)
        
        print("\n🎉 Pipeline completed successfully!")
        print(f"📁 Context Pack: {args.context_output}")
        print(f"📊 MER Schema: {args.mer_output}")
        
        # Show summary
        entities_count = len(mer.get("entities", []))
        relationships_count = len(mer.get("relationships", []))
        print(f"\n📈 Generated {entities_count} entities and {relationships_count} relationships")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()