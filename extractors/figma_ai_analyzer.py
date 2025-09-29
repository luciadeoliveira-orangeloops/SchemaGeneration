#!/usr/bin/env python3
"""
AI-powered Figma data analyzer using OpenAI
"""
import json
import os
import sys
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.openai_client import OpenAIClient

class FigmaAIAnalyzer:
    """Analyzes Figma data using OpenAI to extract entities and relationships"""
    
    def __init__(self):
        self.openai_client = OpenAIClient()
    
    def analyze_figma_data(self, figma_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze raw Figma data using OpenAI to extract entities, attributes and relationships
        """
        print("🤖 Analyzing Figma data with OpenAI...")
        
        # Create the analysis prompt
        analysis_prompt = self._create_analysis_prompt(figma_data)
        
        # Call OpenAI for analysis
        try:
            result = self.openai_client.run_model(
                prompt=analysis_prompt,
                model="gpt-4o",  # Using GPT-4 for better analysis capabilities
                max_tokens=4000
            )
            
            # Parse the result
            analysis_result = self._parse_ai_response(result)
            
            print(f"✅ AI Analysis complete. Found {len(analysis_result.get('entities', []))} entities")
            
            return analysis_result
            
        except Exception as e:
            print(f"❌ Error during AI analysis: {e}")
            return {
                "entities": [],
                "relationships": [],
                "error": str(e)
            }
    
    def _create_analysis_prompt(self, figma_data: Dict[str, Any]) -> str:
        """Create a detailed prompt for OpenAI analysis"""
        
        # Extract component names from the data
        component_names = self._extract_component_names(figma_data)
        
        prompt = f"""
You are an expert data architect analyzing a Figma design file to extract database entities, attributes, and relationships for schema generation.

FIGMA COMPONENT NAMES FOUND:
{json.dumps(component_names, indent=2)}

ANALYSIS INSTRUCTIONS:
1. Analyze the component names above which represent UI screens and features from the Figma design
2. Look for business entities and data objects suggested by these component names:
   - "Inicio de Sesion" suggests USER entity with login capabilities
   - "Crear cuenta" suggests USER entity with registration
   - "Pagina principal" suggests main dashboard or home page
   - "Proyectos" suggests PROJECT entity
   - "Olvido Contraseña" suggests password reset functionality for USER
   - Input, State, Property components suggest form fields and attributes

3. For each identified entity, infer:
   - Entity name (clean, database-appropriate name like User, Project, etc.)
   - Likely attributes based on the UI functionality
   - Relationships between entities

4. Focus on common application entities:
   - User (with login, registration, password reset)
   - Project (suggested by "Proyectos")
   - Session (for login management)
   - Any other entities suggested by the component names

RESPONSE FORMAT:
Return ONLY valid JSON in this exact structure:
{{
  "entities": [
    {{
      "name": "User",
      "attributes": [
        {{
          "name": "id",
          "type": "integer",
          "tags": ["pk"],
          "description": "Primary key for user"
        }},
        {{
          "name": "email",
          "type": "string",
          "tags": ["required", "unique"],
          "description": "User email for login"
        }},
        {{
          "name": "password",
          "type": "string",
          "tags": ["required"],
          "description": "User password hash"
        }}
      ],
      "sources": ["figma:Inicio de Sesion", "figma:Crear cuenta"],
      "ui_context": "Login and registration screens",
      "confidence": 0.9
    }}
  ],
  "relationships": [
    {{
      "from_entity": "User",
      "to_entity": "Project",
      "relationship_type": "one_to_many",
      "description": "Users can have multiple projects",
      "confidence": 0.8
    }}
  ],
  "analysis_notes": [
    "Analysis based on Figma component names suggesting typical web application with user management and projects",
    "Inferred common attributes for each entity based on typical application patterns",
    "High confidence entities: User (login/register screens), Project (proyectos mention)"
  ]
}}

IMPORTANT:
- Analyze the component names as clues to business functionality
- Create realistic entities that would support the UI features shown
- Include standard attributes needed for each entity type
- Focus on the main business objects: Users, Projects, and related entities
- Use high confidence scores for obvious entities like User (from login screens)

Begin analysis:
"""
        return prompt
    
    def _extract_component_names(self, figma_data: Dict[str, Any]) -> List[str]:
        """Extract component names from Figma data"""
        component_names = []
        
        if not figma_data or "content" not in figma_data:
            return component_names
        
        content = figma_data["content"]
        if not isinstance(content, list):
            return component_names
        
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_content = item.get("text", "")
                
                # Parse YAML-like content to extract component names
                if "components:" in text_content:
                    # Split by lines and look for component names
                    lines = text_content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line.startswith("name:"):
                            # Extract name value
                            name = line.replace("name:", "").strip()
                            if name and name not in component_names:
                                component_names.append(name)
                        elif "name:" in line and not line.startswith("#"):
                            # Handle inline name definitions
                            parts = line.split("name:")
                            if len(parts) > 1:
                                name = parts[1].strip()
                                if name and name not in component_names:
                                    component_names.append(name)
        
        return component_names
    
    def _summarize_figma_data(self, figma_data: Dict[str, Any], max_items: int = 100) -> Dict[str, Any]:
        """
        Summarize Figma data to fit within token limits while preserving relevant information
        """
        if not figma_data or "content" not in figma_data:
            return figma_data
        
        content = figma_data["content"]
        if not isinstance(content, list):
            return figma_data
        
        # Extract key information from the first several content items
        summarized_content = []
        
        for i, item in enumerate(content[:max_items]):
            if isinstance(item, dict):
                # Keep text content and key structural information
                summary_item = {
                    "type": item.get("type", "unknown"),
                    "text": item.get("text", "")[:200],  # Limit text length
                }
                
                # Add any additional relevant fields
                for key in ["name", "id", "characters", "componentId"]:
                    if key in item:
                        summary_item[key] = item[key]
                
                summarized_content.append(summary_item)
        
        return {
            "content": summarized_content,
            "total_items": len(content),
            "analyzed_items": len(summarized_content),
            "summary": f"Figma file with {len(content)} elements, analyzing first {len(summarized_content)}"
        }
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI response and extract structured data"""
        try:
            # Clean the response - remove any markdown code blocks
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            # Parse JSON
            result = json.loads(cleaned_response.strip())
            
            # Validate structure
            if not isinstance(result, dict):
                raise ValueError("Response is not a JSON object")
            
            # Ensure required fields exist
            result.setdefault("entities", [])
            result.setdefault("relationships", [])
            result.setdefault("analysis_notes", [])
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            print(f"Raw response: {response[:500]}...")
            return {
                "entities": [],
                "relationships": [],
                "analysis_notes": [f"Failed to parse AI response: {str(e)}"],
                "error": "JSON parsing failed",
                "raw_response": response
            }
        except Exception as e:
            print(f"❌ Error processing AI response: {e}")
            return {
                "entities": [],
                "relationships": [],
                "analysis_notes": [f"Error processing response: {str(e)}"],
                "error": str(e)
            }

def main():
    """Test the AI analyzer"""
    analyzer = FigmaAIAnalyzer()
    
    # Load test data
    try:
        with open("context/figma-raw-data.json", "r") as f:
            figma_data = json.load(f)
        
        # Analyze the data
        result = analyzer.analyze_figma_data(figma_data)
        
        # Save results
        output_path = "context/figma-ai-analysis.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ AI analysis saved to: {output_path}")
        
        # Show summary
        entities = result.get("entities", [])
        relationships = result.get("relationships", [])
        
        print(f"\n📊 ANALYSIS SUMMARY:")
        print(f"   Entities found: {len(entities)}")
        print(f"   Relationships found: {len(relationships)}")
        
        for entity in entities:
            name = entity.get("name", "Unknown")
            attrs = len(entity.get("attributes", []))
            confidence = entity.get("confidence", 0)
            print(f"   📋 {name}: {attrs} attributes (confidence: {confidence:.1f})")
        
        for rel in relationships:
            from_e = rel.get("from_entity", "?")
            to_e = rel.get("to_entity", "?")
            rel_type = rel.get("relationship_type", "unknown")
            print(f"   🔗 {from_e} -> {to_e} ({rel_type})")
        
        if result.get("analysis_notes"):
            print(f"\n📝 ANALYSIS NOTES:")
            for note in result["analysis_notes"]:
                print(f"   • {note}")
        
    except FileNotFoundError:
        print("❌ No figma-raw-data.json found. Run simple_figma_test.py first.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()