PASS_ENTITIES = """TASK
From the CONTEXT PACK, list the canonical domain ENTITIES.

INPUT
- CONTEXT PACK (glossary, Figma entity cards, rules)

OUTPUT (JSON ONLY)
{
  "entities": [
    {
      "name": "User",
      "description": "Short description of what this entity represents",
      "aliases": ["Customer", "Account (UI)"],
      "sources": ["figma:...", "doc:..."],
      "confidence": 0.92
    }
  ],
  "open_questions": [
    "Based on the documentation analysis, specific questions about potential issues or missing entities"
  ]
}

INSTRUCTIONS FOR OPEN_QUESTIONS:
Analyze the context pack and generate SPECIFIC questions based on what you observe:

1. CONFLICTING TERMS: If you see terms that might refer to the same thing or different things, ask: 
   - "Are 'Project' and 'Event' the same entity or distinct entities?"
   - "Should 'Customer' and 'User' be merged into a single entity?"

2. MISSING ENTITIES: If you notice gaps in the domain model, ask:
   - "Should we include a 'Task' entity to track work items within projects?"
   - "Is there a 'Team' or 'Organization' entity missing for multi-user scenarios?"

3. UNCLEAR SCOPE: If entity boundaries are unclear, ask:
   - "Should 'Session' include authentication tokens or just login tracking?"
   - "Does 'Project' include financial/billing information or just metadata?"

4. DOMAIN-SPECIFIC CONCERNS: Based on the specific application context, ask relevant questions:
   - For project management: "Should we track project status/phases?"
   - For e-commerce: "Should we separate 'Product' from 'ProductVariant'?"
   - For social apps: "Should we include 'Notification' or 'Activity' entities?"

DO NOT use generic questions. Instead, analyze the actual content and generate questions that would help clarify the specific domain model being built.

Constraints:
- Use singular PascalCase names for entities.
- Include at least one source per entity.
- Prefer glossary terms over UI labels when they conflict; record the conflict in open_questions[] if needed.
- Generate 2-4 SPECIFIC open_questions based on actual analysis of the context pack.
"""
