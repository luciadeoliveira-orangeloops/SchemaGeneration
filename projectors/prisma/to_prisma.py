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


def map_type_with_db_constraints(type_str: str, attr_name: str = "", context: Dict = None, enums: List[Dict] = None) -> Dict[str, str]:
    """Map MER types to Prisma types with proper database constraints"""
    context = context or {}
    enums = enums or []
    
    # Check if this is an enum type
    enum_names = [enum['name'] for enum in enums]
    if type_str in enum_names:
        # For enum types, don't add database constraints - Prisma handles this automatically
        return {"type": type_str, "db": ""}
    
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
    """Use AI to enhance the Prisma schema following the exact template format provided"""
    
    try:
        llm = OpenAIClient()
        
        # Define the exact template format
        template_schema = '''datasource db {
  provider = "postgresql"
  url      = env("DB_CONNECTION_URL")
}

generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"

  previewFeatures = ["views", "relationJoins"]
  binaryTargets   = ["native"]

  runtime = "nodejs" // nodejs (alias node), edge-light (alias vercel), react-native
}

generator dbml {
  provider = "prisma-dbml-generator"
}

enum UserStatus {
  BLOCKED
  PENDING
  ACTIVE
}

enum UserRole {
  BASIC
  TRUSTED
  ADMINISTRATOR
}

model User {
  id        String  @id @default(uuid()) @db.Uuid
  firstName String? @map("first_name") @db.VarChar(255)
  lastName  String? @map("last_name") @db.VarChar(255)
  email     String  @unique @map("email") @db.VarChar(255)

  status UserStatus @default(ACTIVE)
  role   UserRole   @default(BASIC) @map("role")

  password String

  userRefreshToken UserRefreshToken[]

  createdAt DateTime  @default(now()) @map("created_at")
  updatedAt DateTime  @updatedAt @map("updated_at")
  deletedAt DateTime? @map("deleted_at")

  @@map("user")
}

model UserRefreshToken {
  id      String   @id @default(uuid()) @db.Uuid
  userId  String   @map("user_id") @db.Uuid
  token   String
  enabled Boolean? @default(true)

  user User @relation(fields: [userId], references: [id])

  createdAt DateTime  @default(now()) @map("created_at") @db.Timestamptz(6)
  updatedAt DateTime  @updatedAt @map("updated_at") @db.Timestamptz(6)
  deletedAt DateTime? @map("deleted_at") @db.Timestamptz(6)

  @@map("user_refresh_token")
}

enum FileStatus {
  PENDING_UPLOAD
  READY
  INVALID
}

enum FileType {
  OTHER
}

model File {
  id          String     @id @default(uuid())
  path        String     @db.VarChar(255)
  name        String     @db.VarChar(255)
  isPrivate   Boolean    @default(false) @map("is_private")
  status      FileStatus @default(PENDING_UPLOAD)
  type        FileType   @default(OTHER)
  extension   String?    @db.VarChar(255)
  contentType String?    @map("content_type") @db.VarChar(255)
  size        Int?
  notes       String?

  createdAt DateTime  @default(now()) @map("created_at")
  updatedAt DateTime  @updatedAt @map("updated_at")
  deletedAt DateTime? @map("deleted_at")

  @@map("file")
}

enum TaskPriority {
  LOW
  MEDIUM
  HIGH
}

model Task {
  id String @id @default(uuid())

  title       String
  description String?
  completed   Boolean      @default(false)
  dueDate     DateTime?    @map("due_date")
  priority    TaskPriority @default(MEDIUM)

  createdAt DateTime  @default(now()) @map("created_at")
  updatedAt DateTime  @updatedAt @map("updated_at")
  deletedAt DateTime? @map("deleted_at")

  @@map("task")
}'''
        
        prompt = f"""You are a Prisma schema expert. I need you to generate a Prisma schema based on MER data, but following EXACTLY the format and style of the provided template.

Here's the MER data to process:
```json
{json.dumps(mer_data, indent=2)}
```

Here's the EXACT template format you MUST follow as STYLE REFERENCE:
```prisma
{template_schema}
```

CRITICAL REQUIREMENTS:

1. **PRESERVE EXACTLY**: Keep User and UserRefreshToken models EXACTLY as shown in the template. Only ADD new fields if they appear in the MER data for these entities, but maintain the existing format, order, and style.

2. **DO NOT INCLUDE**: File and Task models from the template. These are ONLY style examples. Do not include them in the final schema.

3. **Template Format**: Follow the exact same formatting style, spacing, and structure as the template for all new models and enums.

4. **Enum Format**: 
   - Values in UPPER_SNAKE_CASE
   - No @db annotations on enum types
   - Default values like @default(ACTIVE)
   - Only include UserStatus and UserRole enums from template, plus any new enums from MER data

5. **Model Format**:
   - IDs: String @id @default(uuid()) @db.Uuid (except when specific @db.Uuid is not needed)
   - String fields: @db.VarChar(255) for names, emails, etc.
   - Text fields: No @db annotation (let Prisma handle)
   - Field mapping: @map("snake_case")
   - Table mapping: @@map("snake_case")
   - Standard timestamps: createdAt, updatedAt, deletedAt with exact format from template

6. **Relationships**: Use the same style as the UserRefreshToken example.

7. **Generate new models/enums** that appear in the MER data but are not User or UserRefreshToken.

8. **Final structure**: datasource, generators, UserStatus, UserRole, User, UserRefreshToken, then any new enums and models from MER data.

Please return ONLY the complete Prisma schema following this exact template format, but WITHOUT File and Task models.
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


def generate_models(entities: List[Dict], relationships: List[Dict], enums: List[Dict] = None) -> str:
    """Generate Prisma models from entities and relationships with enhanced formatting"""
    result = []
    enums = enums or []
    
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
    
    # Create enum value mapping for defaults
    enum_defaults = {}
    for enum in enums:
        enum_name = enum['name']
        values = enum.get('values', [])
        if values:
            # Convert to proper enum format and pick a sensible default
            enhanced_values = enhance_enum_values(values)
            if enum_name == 'ProjectPriority' and 'MEDIUM' in enhanced_values:
                default_value = 'MEDIUM'
            elif enum_name == 'UserRole' and 'USER' in enhanced_values:
                default_value = 'USER'
            else:
                default_value = enhanced_values[0]  # First value as default
            enum_defaults[enum_name] = default_value
    
    for entity in entities:
        name = entity['name']
        result.append(f"model {name} {{")
        
        # Add regular attributes
        for attr in entity.get('attributes', []):
            attr_name = attr['name']
            type_info = map_type_with_db_constraints(attr.get('type', 'string'), attr_name, enums=enums)
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
            elif attr_type in enum_defaults and not attr.get('pk', False):
                # Add default value for enum types
                default_enum_val = enum_defaults[attr_type]
                decorators.append(f"@default({default_enum_val})")
            
            # Add field mapping
            snake_name = to_snake_case(attr_name)
            if snake_name != attr_name.lower():
                decorators.append(f'@map("{snake_name}")')
            
            # Add database constraint (but not for enums)
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
    """Convert MER data to Prisma schema using template format and AI enhancement"""
    
    # Use AI enhancement by default since we want to follow the exact template
    if use_ai:
        # Pass empty base schema since AI will use the embedded template
        return enhance_schema_with_ai(mer_data, "")
    else:
        # If AI is disabled, create a basic schema following template format
        schema_parts = []
        
        # Header with template configuration
        schema_parts.append("""datasource db {
  provider = "postgresql"
  url      = env("DB_CONNECTION_URL")
}

generator client {
  provider = "prisma-client"
  output   = "../src/generated/prisma"

  previewFeatures = ["views", "relationJoins"]
  binaryTargets   = ["native"]

  runtime = "nodejs" // nodejs (alias node), edge-light (alias vercel), react-native
}

generator dbml {
  provider = "prisma-dbml-generator"
}

""")
        
        # Include only the essential base enums and models (no File/Task)
        base_template = '''enum UserStatus {
  BLOCKED
  PENDING
  ACTIVE
}

enum UserRole {
  BASIC
  TRUSTED
  ADMINISTRATOR
}

model User {
  id        String  @id @default(uuid()) @db.Uuid
  firstName String? @map("first_name") @db.VarChar(255)
  lastName  String? @map("last_name") @db.VarChar(255)
  email     String  @unique @map("email") @db.VarChar(255)

  status UserStatus @default(ACTIVE)
  role   UserRole   @default(BASIC) @map("role")

  password String

  userRefreshToken UserRefreshToken[]

  createdAt DateTime  @default(now()) @map("created_at")
  updatedAt DateTime  @updatedAt @map("updated_at")
  deletedAt DateTime? @map("deleted_at")

  @@map("user")
}

model UserRefreshToken {
  id      String   @id @default(uuid()) @db.Uuid
  userId  String   @map("user_id") @db.Uuid
  token   String
  enabled Boolean? @default(true)

  user User @relation(fields: [userId], references: [id])

  createdAt DateTime  @default(now()) @map("created_at") @db.Timestamptz(6)
  updatedAt DateTime  @updatedAt @map("updated_at") @db.Timestamptz(6)
  deletedAt DateTime? @map("deleted_at") @db.Timestamptz(6)

  @@map("user_refresh_token")
}

'''
        
        schema_parts.append(base_template)
        
        # Add any additional models from MER that aren't in the base template
        entities = mer_data.get('entities', [])
        template_models = ['User', 'UserRefreshToken']  # Only these are preserved
        
        for entity in entities:
            if entity['name'] not in template_models:
                # Generate additional models following template style
                models_schema = generate_models([entity], mer_data.get('relationships', []), mer_data.get('enums', []))
                schema_parts.append(models_schema)
        
        return "".join(schema_parts)


def main():
    """Main function to convert MER to Prisma schema"""
    
    # Parse command line arguments
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    use_ai = "--no-ai" not in sys.argv
    
    if use_ai:
        print("🤖 Using AI enhancement (use --no-ai to disable)")
    else:
        print("⚙️ Using rule-based generation only")
    
    # Determine input and output files
    if len(args) >= 1:
        mer_file = args[0]
    else:
        mer_file = "schema/mer.json"
        
    if len(args) >= 2:
        output_file = args[1]
    else:
        output_file = "schema/schema.prisma"
    
    print(f"📖 Input MER file: {mer_file}")
    print(f"💾 Output Prisma file: {output_file}")
    
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
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
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
