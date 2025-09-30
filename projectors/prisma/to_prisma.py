#!/usr/bin/env python3
"""
Convert MER JSON schema to Prisma schema with AI enhancement
"""

import json
import sys
import os
from typing import Dict, Any, List, Optional
import uuid

# Import LLM client
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from llm.openai_client import OpenAIClient


def map_type_with_db_constraints(type_str: str, attr_name: str = "", context: Dict = None) -> Dict[str, str]:
    """Map MER types to Prisma types with proper database constraints"""
    context = context or {}
    
    type_mapping = {
        "string": {"type": "String", "db": "@db.VarChar(255)"},
        "text": {"type": "String", "db": "@db.Text"},
        "int": {"type": "Int", "db": ""},
        "integer": {"type": "Int", "db": ""},
        "bigint": {"type": "BigInt", "db": ""},
        "float": {"type": "Float", "db": ""},
        "decimal": {"type": "Decimal", "db": "@db.Decimal(10,2)"},
        "boolean": {"type": "Boolean", "db": ""},
        "bool": {"type": "Boolean", "db": ""},
        "date": {"type": "DateTime", "db": "@db.Date"},
        "datetime": {"type": "DateTime", "db": "@db.Timestamptz(6)"},
        "timestamp": {"type": "DateTime", "db": "@db.Timestamptz(6)"},
        "uuid": {"type": "String", "db": "@db.Uuid"},
        "cuid": {"type": "String", "db": ""},
        "json": {"type": "Json", "db": "@db.JsonB"},
        "email": {"type": "String", "db": "@db.VarChar(255)"},
        "url": {"type": "String", "db": "@db.VarChar(500)"},
    }
    
    base_type = type_str.lower() if type_str else "string"
    result = type_mapping.get(base_type, {"type": "String", "db": "@db.VarChar(255)"})
    
    # Special handling for IDs
    if attr_name.lower() in ['id'] or attr_name.lower().endswith('id'):
        result = {"type": "String", "db": "@db.Uuid"}
    
    # Special handling based on attribute name patterns
    if 'password' in attr_name.lower():
        result = {"type": "String", "db": "@db.VarChar(255)"}
    elif 'email' in attr_name.lower():
        result = {"type": "String", "db": "@db.VarChar(255)"}
    elif 'name' in attr_name.lower():
        result = {"type": "String", "db": "@db.VarChar(255)"}
    elif 'description' in attr_name.lower():
        result = {"type": "String", "db": "@db.Text"}
    elif attr_name.lower() in ['createdat', 'created_at']:
        result = {"type": "DateTime", "db": "@db.Timestamptz(6)"}
    elif attr_name.lower() in ['updatedat', 'updated_at']:
        result = {"type": "DateTime", "db": "@db.Timestamptz(6)"}
    elif attr_name.lower() in ['deletedat', 'deleted_at']:
        result = {"type": "DateTime", "db": "@db.Timestamptz(6)"}
    
    return result


def to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case"""
    result = ""
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result += "_"
        result += char.lower()
    return result


def generate_standard_fields() -> List[Dict]:
    """Generate standard audit fields that should be added to all models"""
    return [
        {
            "name": "createdAt",
            "type": "DateTime",
            "nullable": False,
            "default": "now()",
            "map": "created_at",
            "db": "@db.Timestamptz(6)"
        },
        {
            "name": "updatedAt", 
            "type": "DateTime",
            "nullable": False,
            "updatedAt": True,
            "map": "updated_at",
            "db": "@db.Timestamptz(6)"
        },
        {
            "name": "deletedAt",
            "type": "DateTime", 
            "nullable": True,
            "map": "deleted_at",
            "db": "@db.Timestamptz(6)"
        }
    ]


def enhance_enum_values(enum_values: List[str]) -> List[str]:
    """Enhance enum values to follow proper naming conventions"""
    enhanced = []
    for value in enum_values:
        # Convert to UPPER_SNAKE_CASE
        clean_value = value.replace("-", "_").replace(" ", "_").upper()
        enhanced.append(clean_value)
    return enhanced


def enhance_schema_with_ai(mer_data: Dict[str, Any], base_schema: str) -> str:
    """Use AI to enhance the Prisma schema with best practices and improvements"""
    
    try:
        llm = OpenAIClient()
        
        prompt = f"""You are a Prisma schema expert. I have a base Prisma schema generated from a MER model, but I want you to enhance it with best practices, proper constraints, and professional formatting.

Here's the original MER data for context:
```json
{json.dumps(mer_data, indent=2)}
```

Here's the base Prisma schema:
```prisma
{base_schema}
```

Please enhance this schema following these guidelines:

1. **Field Types & Constraints**: 
   - Use appropriate database types (@db.VarChar with proper lengths, @db.Text for long content, @db.Uuid for IDs)
   - Add proper constraints based on field names and context
   - Email fields should be @db.VarChar(255) with validation
   - Names should be @db.VarChar(255)
   - Descriptions should be @db.Text

2. **Standard Fields**: Every model should have:
   - createdAt DateTime @default(now()) @map("created_at") @db.Timestamptz(6)
   - updatedAt DateTime @updatedAt @map("updated_at") @db.Timestamptz(6)  
   - deletedAt DateTime? @map("deleted_at") @db.Timestamptz(6)

3. **IDs**: All primary keys should be:
   - String @id @default(uuid()) @db.Uuid

4. **Field Mapping**: Convert camelCase to snake_case with @map():
   - userId -> @map("user_id")
   - firstName -> @map("first_name")

5. **Table Mapping**: All models should have @@map("table_name") in snake_case

6. **Enums**: Values should be UPPER_SNAKE_CASE

7. **Relationships**: 
   - Foreign keys should be String @db.Uuid
   - Proper @relation() declarations
   - Include reverse relationships

8. **Defaults**: Add sensible defaults where appropriate

9. **Comments**: Add helpful comments for complex relationships

Please return ONLY the enhanced Prisma schema, nothing else. Make sure it's valid Prisma syntax.
"""

        print("🤖 Enhancing Prisma schema with AI...")
        
        response = llm.run_model(
            prompt=prompt,
            model="gpt-4o",
            max_tokens=4000,
            temperature=0.1
        )
        
        # Extract the schema from the response
        enhanced_schema = response.strip()
        
        # Clean up the response if it contains markdown formatting
        if "```prisma" in enhanced_schema:
            start = enhanced_schema.find("```prisma") + 9
            end = enhanced_schema.find("```", start)
            if end != -1:
                enhanced_schema = enhanced_schema[start:end].strip()
        elif "```" in enhanced_schema:
            start = enhanced_schema.find("```") + 3
            end = enhanced_schema.find("```", start)
            if end != -1:
                enhanced_schema = enhanced_schema[start:end].strip()
        
        print("✅ AI enhancement completed successfully")
        return enhanced_schema
        
    except Exception as e:
        print(f"⚠️ AI enhancement failed: {e}")
        print("🔄 Falling back to base schema")
        return base_schema


def generate_enums(enums: List[Dict]) -> str:
    """Generate Prisma enums with enhanced formatting"""
    if not enums:
        return ""
    
    result = []
    for enum in enums:
        result.append(f"enum {enum['name']} {{")
        enhanced_values = enhance_enum_values(enum['values'])
        for value in enhanced_values:
            result.append(f"  {value}")
        result.append("}")
        result.append("")
    
    return "\n".join(result)


def generate_models(entities: List[Dict], relationships: List[Dict]) -> str:
    """Generate Prisma models from entities and relationships with enhanced formatting"""
    result = []
    
    # Build relationship mapping
    rel_map = {}
    for rel in relationships:
        from_entity = rel['from']
        to_entity = rel['to']
        fk_info = rel.get('fk', {})
        
        if from_entity not in rel_map:
            rel_map[from_entity] = []
        
        rel_map[from_entity].append({
            'to': to_entity,
            'type': rel['type'],
            'fk_attribute': fk_info.get('attribute', f"{to_entity.lower()}Id"),
            'ref_field': fk_info.get('ref', 'User.id').split('.')[-1]
        })
    
    for entity in entities:
        name = entity['name']
        result.append(f"model {name} {{")
        
        # Add regular attributes
        for attr in entity.get('attributes', []):
            attr_name = attr['name']
            type_info = map_type_with_db_constraints(attr.get('type', 'string'), attr_name)
            attr_type = type_info['type']
            db_constraint = type_info['db']
            
            # Handle nullable
            if attr.get('nullable', False):
                attr_type += "?"
            
            # Build decorators
            decorators = []
            if attr.get('pk', False):
                decorators.append("@id")
                decorators.append("@default(uuid())")
            if attr.get('unique', False):
                decorators.append("@unique")
            if attr.get('default') and not attr.get('pk', False):
                default_val = attr['default']
                if default_val in ['now()', 'true', 'false']:
                    decorators.append(f"@default({default_val})")
                else:
                    decorators.append(f'@default("{default_val}")')
            
            # Add field mapping
            snake_name = to_snake_case(attr_name)
            if snake_name != attr_name.lower():
                decorators.append(f'@map("{snake_name}")')
            
            # Add database constraint
            if db_constraint:
                decorators.append(db_constraint)
            
            decorator_str = " " + " ".join(decorators) if decorators else ""
            result.append(f"  {attr_name} {attr_type}{decorator_str}")
        
        # Add relationship fields
        if name in rel_map:
            result.append("")  # Blank line before relationships
            for rel in rel_map[name]:
                to_entity = rel['to']
                fk_attr = rel['fk_attribute']
                ref_field = rel['ref_field']
                
                # Add the foreign key field if not already present
                fk_exists = any(attr['name'] == fk_attr for attr in entity.get('attributes', []))
                if not fk_exists:
                    snake_fk = to_snake_case(fk_attr)
                    map_decorator = f' @map("{snake_fk}")' if snake_fk != fk_attr.lower() else ""
                    result.append(f"  {fk_attr} String{map_decorator} @db.Uuid")
                
                # Add the relation field
                relation_name = to_entity.lower()
                result.append(f"  {relation_name} {to_entity} @relation(fields: [{fk_attr}], references: [{ref_field}])")
        
        # Add reverse relationships (one-to-many)
        reverse_rels = []
        for other_entity in entities:
            if other_entity['name'] in rel_map:
                for rel in rel_map[other_entity['name']]:
                    if rel['to'] == name:
                        # This entity is referenced by other_entity
                        reverse_field = f"{other_entity['name'].lower()}s"
                        reverse_rels.append(f"  {reverse_field} {other_entity['name']}[]")
        
        if reverse_rels:
            result.append("")  # Blank line before reverse relationships
            result.extend(reverse_rels)
        
        # Add standard audit fields
        standard_fields = generate_standard_fields()
        has_audit_fields = any(attr['name'] in ['createdAt', 'updatedAt', 'deletedAt'] 
                              for attr in entity.get('attributes', []))
        
        if not has_audit_fields:
            result.append("")  # Blank line before audit fields
            for field in standard_fields:
                decorators = []
                if field.get('default'):
                    if field['default'] == 'now()':
                        decorators.append("@default(now())")
                    else:
                        decorators.append(f"@default({field['default']})")
                if field.get('updatedAt'):
                    decorators.append("@updatedAt")
                if field.get('map'):
                    decorators.append(f'@map("{field["map"]}")')
                if field.get('db'):
                    decorators.append(field['db'])
                
                nullable = "?" if field['nullable'] else ""
                decorator_str = " " + " ".join(decorators) if decorators else ""
                result.append(f"  {field['name']} {field['type']}{nullable}{decorator_str}")
        
        # Add table mapping
        table_name = to_snake_case(name)
        result.append("")
        result.append(f'  @@map("{table_name}")')
        result.append("}")
        result.append("")
    
    return "\n".join(result)


def mer_to_prisma(mer_data: Dict[str, Any], use_ai: bool = True) -> str:
    """Convert MER data to Prisma schema with professional formatting and AI enhancement"""
    
    schema_parts = []
    
    # Header with professional configuration
    schema_parts.append("""// Generated from MER schema
datasource db {
  provider = "postgresql"
  url      = env("DB_CONNECTION_URL")
}

generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"

  previewFeatures = ["views", "relationJoins"]
  binaryTargets   = ["native"]

  runtime = "nodejs"
}

generator dbml {
  provider = "prisma-dbml-generator"
}

""")
    
    # Enums
    enums = mer_data.get('enums', [])
    if enums:
        enum_schema = generate_enums(enums)
        schema_parts.append(enum_schema)
    
    # Models
    entities = mer_data.get('entities', [])
    relationships = mer_data.get('relationships', [])
    
    if entities:
        models_schema = generate_models(entities, relationships)
        schema_parts.append(models_schema)
    
    base_schema = "".join(schema_parts)
    
    # Enhance with AI if requested
    if use_ai:
        return enhance_schema_with_ai(mer_data, base_schema)
    else:
        return base_schema


def main():
    """Main function to convert MER to Prisma schema"""
    
    # Check command line arguments for AI flag
    use_ai = "--no-ai" not in sys.argv
    
    if use_ai:
        print("🤖 Using AI enhancement (use --no-ai to disable)")
    else:
        print("⚙️ Using rule-based generation only")
    
    # Load MER schema
    mer_file = "schema/mer.json"
    if not os.path.exists(mer_file):
        print(f"❌ Error: {mer_file} not found")
        sys.exit(1)
    
    try:
        with open(mer_file, 'r') as f:
            mer_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading {mer_file}: {e}")
        sys.exit(1)
    
    # Generate Prisma schema
    try:
        prisma_schema = mer_to_prisma(mer_data, use_ai=use_ai)
    except Exception as e:
        print(f"❌ Error generating Prisma schema: {e}")
        sys.exit(1)
    
    # Save Prisma schema
    output_file = "schema/schema.prisma"
    os.makedirs("schema", exist_ok=True)
    
    try:
        with open(output_file, 'w') as f:
            f.write(prisma_schema)
        print(f"✅ Prisma schema generated successfully!")
        print(f"📄 Saved to: {output_file}")
        
        # Show summary
        lines = prisma_schema.split('\n')
        model_count = len([line for line in lines if line.startswith('model ')])
        enum_count = len([line for line in lines if line.startswith('enum ')])
        
        print(f"📊 Generated schema contains:")
        print(f"   • {model_count} models")
        print(f"   • {enum_count} enums")
        
        if use_ai:
            print("   • AI-enhanced with professional formatting")
        else:
            print("   • Rule-based generation with standard formatting")
            
    except Exception as e:
        print(f"❌ Error saving {output_file}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
