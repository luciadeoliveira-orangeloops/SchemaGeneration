#!/usr/bin/env python3
"""
Convert MER JSON schema to Prisma schema
"""

import json
import sys
import os
from typing import Dict, Any, List


def map_type(type_str: str) -> str:
    """Map MER types to Prisma types"""
    type_map = {
        "string": "String",
        "text": "String", 
        "int": "Int",
        "integer": "Int",
        "bigint": "BigInt",
        "float": "Float",
        "decimal": "Decimal",
        "boolean": "Boolean",
        "bool": "Boolean",
        "date": "DateTime",
        "datetime": "DateTime",
        "timestamp": "DateTime",
        "uuid": "String",
        "cuid": "String", 
        "json": "Json",
        "email": "String",
        "url": "String",
    }
    return type_map.get(type_str.lower() if type_str else "string", "String")


def generate_enums(enums: List[Dict]) -> str:
    """Generate Prisma enums"""
    if not enums:
        return ""
    
    result = []
    for enum in enums:
        result.append(f"enum {enum['name']} {{")
        for value in enum['values']:
            # Clean up enum values for Prisma
            clean_value = value.replace("-", "_").replace(" ", "_").upper()
            result.append(f"  {clean_value}")
        result.append("}")
        result.append("")
    
    return "\n".join(result)


def generate_models(entities: List[Dict], relationships: List[Dict]) -> str:
    """Generate Prisma models from entities and relationships"""
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
        
        # Add attributes
        for attr in entity.get('attributes', []):
            attr_name = attr['name']
            attr_type = map_type(attr.get('type', 'string'))
            
            # Handle nullable
            if attr.get('nullable', False):
                attr_type += "?"
            
            # Build decorators
            decorators = []
            if attr.get('pk', False):
                decorators.append("@id")
            if attr.get('unique', False):
                decorators.append("@unique")
            if attr.get('default'):
                decorators.append(f"@default({attr['default']})")
            
            decorator_str = " " + " ".join(decorators) if decorators else ""
            result.append(f"  {attr_name} {attr_type}{decorator_str}")
        
        # Add relationships
        if name in rel_map:
            for rel in rel_map[name]:
                to_entity = rel['to']
                fk_attr = rel['fk_attribute']
                ref_field = rel['ref_field']
                
                # Add the relation field
                relation_name = to_entity.lower()
                result.append(f"  {relation_name} {to_entity} @relation(fields: [{fk_attr}], references: [{ref_field}])")
                
                # Add the foreign key field if not already present
                fk_exists = any(attr['name'] == fk_attr for attr in entity.get('attributes', []))
                if not fk_exists:
                    result.append(f"  {fk_attr} String")
        
        # Add reverse relationships (one-to-many)
        for other_entity in entities:
            if other_entity['name'] in rel_map:
                for rel in rel_map[other_entity['name']]:
                    if rel['to'] == name:
                        # This entity is referenced by other_entity
                        reverse_field = f"{other_entity['name'].lower()}s"
                        result.append(f"  {reverse_field} {other_entity['name']}[]")
        
        result.append("}")
        result.append("")
    
    return "\n".join(result)


def mer_to_prisma(mer_data: Dict[str, Any]) -> str:
    """Convert MER data to Prisma schema"""
    
    schema_parts = []
    
    # Header
    schema_parts.append("""// Generated from MER schema
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
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
    
    return "".join(schema_parts)


def main():
    """Main function to convert MER to Prisma schema"""
    
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
        prisma_schema = mer_to_prisma(mer_data)
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
    except Exception as e:
        print(f"❌ Error saving {output_file}: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
