#!/usr/bin/env python3
"""
Full Schema Generation Pipeline

This script runs the complete end-to-end process:
1. Extract documents + Figma data
2. Generate initial MER schema
3. Interactive refinement (questions & answers)
4. Generate refined MER schema  
5. Generate Prisma schema from refined MER

Usage:
    python full_pipeline.py
    
The script will guide you through each step interactively.
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def print_step(step_num: int, title: str, description: str = ""):
    """Print a formatted step header"""
    print(f"\n{'='*60}")
    print(f"🚀 STEP {step_num}: {title}")
    if description:
        print(f"   {description}")
    print('='*60)


def run_command(command: List[str], description: str) -> bool:
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {' '.join(command)}")
        print(f"   Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False


def check_file_exists(filepath: str, description: str) -> bool:
    """Check if a file exists and report status"""
    if os.path.exists(filepath):
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description} not found: {filepath}")
        return False


def get_user_confirmation(message: str, default: bool = True) -> bool:
    """Get user confirmation for proceeding"""
    default_str = "(Y/n)" if default else "(y/N)"
    try:
        response = input(f"\n{message} {default_str}: ").lower().strip()
        if not response:
            return default
        return response in ['y', 'yes']
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Process cancelled by user.")
        return False


def display_file_summary(filepath: str, file_type: str):
    """Display a summary of a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if file_type == "mer":
            entities = data.get('entities', [])
            relationships = data.get('relationships', [])
            enums = data.get('enums', [])
            print(f"📊 MER Summary:")
            print(f"   • Entities: {len(entities)}")
            print(f"   • Relationships: {len(relationships)}")
            print(f"   • Enums: {len(enums)}")
            
            for entity in entities:
                name = entity.get('name', 'Unknown')
                attrs = len(entity.get('attributes', []))
                print(f"     - {name}: {attrs} attributes")
                
        elif file_type == "context":
            docs = data.get('documents', {})
            figma = data.get('figma', {})
            print(f"📊 Context Summary:")
            print(f"   • Document terms: {len(docs.get('glossary', []))}")
            print(f"   • Document rules: {len(docs.get('rules', []))}")
            print(f"   • Document enums: {len(docs.get('enums', []))}")
            print(f"   • Figma components: {len(figma.get('components', []))}")
                
    except Exception as e:
        print(f"⚠️ Could not read {file_type} file: {e}")


def main():
    """Main full pipeline execution"""
    print("🎯 FULL SCHEMA GENERATION PIPELINE")
    print("==================================")
    print("This will run the complete process:")
    print("1. Extract documents + Figma data")
    print("2. Generate initial MER schema")
    print("3. Interactive refinement")
    print("4. Generate Prisma schema")
    print()
    
    if not get_user_confirmation("🚀 Start the full pipeline?"):
        print("👋 Pipeline cancelled.")
        return
    
    # Define file paths
    context_file = "context/context-pack.json"
    initial_mer = "schema/mer.json"
    refined_mer = "schema/mer2.json"
    prisma_schema = "schema/schema.prisma"
    
    # Step 1: Extract Documents + Figma Data
    print_step(1, "DATA EXTRACTION", "Extract documents and Figma data")
    
    if not run_command(["python", "ai_to_schema.py"], "Extracting data and generating initial MER"):
        print("❌ Data extraction failed. Cannot continue.")
        return
    
    # Verify context and initial MER were created
    if not check_file_exists(context_file, "Context pack"):
        print("❌ Context pack not generated. Cannot continue.")
        return
        
    if not check_file_exists(initial_mer, "Initial MER schema"):
        print("❌ Initial MER schema not generated. Cannot continue.")
        return
    
    # Display summaries
    print(f"\n📋 Generated files:")
    display_file_summary(context_file, "context")
    display_file_summary(initial_mer, "mer")
    
    if not get_user_confirmation("🔄 Proceed to interactive refinement?"):
        print("⏭️ Skipping refinement. Pipeline stopped.")
        return
    
    # Step 2: Interactive Refinement
    print_step(2, "INTERACTIVE REFINEMENT", "Answer questions to improve the schema")
    
    print("🎯 Starting interactive refinement...")
    print("💡 You'll be asked questions about your schema.")
    print("💡 Answer the ones you want, skip the others.")
    print()
    
    # Run interactive refinement
    try:
        # Import and run the interactive refinement directly
        from pipeline.interactive_refinement import main as refinement_main
        
        # Temporarily change sys.argv to pass the correct files
        original_argv = sys.argv[:]
        sys.argv = ["interactive_refinement.py", initial_mer, refined_mer]
        
        refinement_main()
        
        # Restore original argv
        sys.argv = original_argv
        
    except KeyboardInterrupt:
        print("\n👋 Refinement cancelled by user.")
        print("⏭️ Continuing with original schema...")
        # Copy original schema as refined schema
        import shutil
        shutil.copy2(initial_mer, refined_mer)
    except Exception as e:
        print(f"❌ Interactive refinement failed: {e}")
        print("⏭️ Continuing with original schema...")
        # Copy original schema as refined schema
        import shutil
        shutil.copy2(initial_mer, refined_mer)
    
    # Verify refined MER exists
    if not check_file_exists(refined_mer, "Refined MER schema"):
        print("⚠️ Using initial MER as refined MER...")
        import shutil
        shutil.copy2(initial_mer, refined_mer)
    
    # Display refined schema summary
    print(f"\n📋 Refined schema:")
    display_file_summary(refined_mer, "mer")
    
    if not get_user_confirmation("🔄 Proceed to Prisma schema generation?"):
        print("⏭️ Skipping Prisma generation. Pipeline stopped.")
        return
    
    # Step 3: Generate Prisma Schema
    print_step(3, "PRISMA SCHEMA GENERATION", "Generate Prisma schema from refined MER")
    
    if not run_command(["python", "projectors/prisma/to_prisma.py", refined_mer, prisma_schema], 
                      f"Generating Prisma schema from {refined_mer}"):
        print("❌ Prisma schema generation failed.")
        return
    
    # Verify Prisma schema was created
    if not check_file_exists(prisma_schema, "Prisma schema"):
        print("❌ Prisma schema not generated.")
        return
    
    # Display Prisma schema preview
    try:
        with open(prisma_schema, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"\n📄 Generated Prisma Schema Preview:")
        print("─" * 50)
        # Show first 1000 characters
        preview = content[:1000]
        print(preview)
        if len(content) > 1000:
            print("...")
            print(f"({len(content)} total characters)")
        print("─" * 50)
        
    except Exception as e:
        print(f"⚠️ Could not preview Prisma schema: {e}")
    
    # Final Success Summary
    print(f"\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)
    print(f"📁 Generated files:")
    print(f"   • Context pack: {context_file}")
    print(f"   • Initial MER: {initial_mer}")
    print(f"   • Refined MER: {refined_mer}")
    print(f"   • Prisma schema: {prisma_schema}")
    print()
    print(f"✅ Next steps:")
    print(f"   • Review schemas: cat {refined_mer}")
    print(f"   • Use Prisma schema: cat {prisma_schema}")
    print(f"   • Run pipeline again: python full_pipeline.py")
    print(f"   • Refine further: python pipeline/interactive_refinement.py {refined_mer}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Pipeline cancelled by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Pipeline failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)