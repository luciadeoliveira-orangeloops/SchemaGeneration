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
  "open_questions": []
}
Constraints:
- Use singular PascalCase names for entities.
- Include at least one source per entity.
- Prefer glossary terms over UI labels when they conflict; record the conflict in open_questions[] if needed.
"""
