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
  "open_questions": []
}
Constraints:
- Use evidence precedence: documents > glossary > Figma connectors > UI labels.
- Include sources[] and confidence on every relationship.
- If cardinality is ambiguous, choose a conservative default (one-to-many), lower the confidence, and add an open question.
"""
