#!/usr/bin/env python3
"""
Batch processing script for multiple Figma projects
"""
import json
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from generate_from_figma import generate_context_pack_from_multiple_figma_files, run_full_pipeline, ensure_directories

def load_projects_config(config_path: str = "figma-projects.json"):
    """Load projects configuration"""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def process_project(project: dict):
    """Process a single project"""
    print(f"\n🚀 Processing project: {project['name']}")
    print(f"📝 Description: {project['description']}")
    print(f"📁 Figma files: {len(project['figma_files'])}")
    
    try:
        # Generate context pack from multiple files
        generate_context_pack_from_multiple_figma_files(
            project['figma_files'],
            project['context_output']
        )
        
        # Run the full pipeline
        run_full_pipeline(
            project['context_output'],
            project['mer_output']
        )
        
        print(f"✅ Project {project['name']} completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Project {project['name']} failed: {e}")
        return False

def main():
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "figma-projects.json"
    
    ensure_directories()
    
    try:
        config = load_projects_config(config_path)
        projects = config.get("projects", [])
        
        print(f"📋 Processing {len(projects)} projects...")
        
        successful = 0
        failed = 0
        
        for project in projects:
            if process_project(project):
                successful += 1
            else:
                failed += 1
        
        print(f"\n🎉 Batch processing completed!")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        
        if failed > 0:
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()