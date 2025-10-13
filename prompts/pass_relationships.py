PASS_RELATIONSHIPS = """TASK
Identify RELATIONSHIPS between entities, including cardinalities and foreign keys (FKs).

RULES
- Express cardinalities as one-to-one, one-to-many, or many-to-many.
- For many-to-many, propose a join table unless an explicit artifact already exists.
- Specify the FK attribute on the referencing side and its reference target (Entity.attr).
- Include mandatory flags if the relationship implies required participation.

OUTPUT (JSON ONLY)
{
  "relationships": [
    {
      "from": "Order",
      "to": "User",
      "type": "many-to-one",
      "fk": {"attribute":"userId","ref":"User.id"},
      "mandatory": {"from": true, "to": false},
      "sources": ["figma:...", "doc:..."],
      "confidence": 0.86
    }
  ],
  "open_questions": [
    "Based on the domain analysis, specific questions about relationships and the overall schema"
  ]
}

INSTRUCTIONS FOR OPEN_QUESTIONS:
Analyze the entities and domain to generate SPECIFIC relationship and schema questions:

1. MISSING RELATIONSHIPS: Based on the domain logic, ask:

2. CARDINALITY QUESTIONS: When relationships are unclear, ask:

3. BUSINESS LOGIC GAPS: Based on the application context, ask:

4. DATA CONSISTENCY: Ask about referential integrity:

5. DOMAIN-SPECIFIC RELATIONSHIPS: Based on the specific application:

6. OVERALL SCHEMA VALIDATION: Always include this general question:

DO NOT use only generic questions. Generate 4-6 SPECIFIC questions based on actual domain analysis.

Constraints:
- Use evidence precedence: documents > glossary > Figma connectors > UI labels.
- Include sources[] and confidence on every relationship.
- If cardinality is ambiguous, choose a conservative default (one-to-many), lower the confidence, and add an open question.
- Generate SPECIFIC open_questions based on actual analysis of the domain and relationships.
"""
