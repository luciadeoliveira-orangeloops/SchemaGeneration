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
   - "Should there be a relationship between Project and Session (e.g., tracking which projects are accessed in each session)?"
   - "Do we need a many-to-many relationship for Project collaborators/team members?"
   - "Should there be self-referencing relationships (e.g., User manager, Project parent/child)?"

2. CARDINALITY QUESTIONS: When relationships are unclear, ask:
   - "Can a Project have multiple owners/managers, or just one User?"
   - "Should Session be one-per-user or allow multiple concurrent sessions?"
   - "Are Projects shared between Users or strictly owned by one User?"

3. BUSINESS LOGIC GAPS: Based on the application context, ask:
   - "Should we track Project history/versions with a separate entity?"
   - "Do we need audit trails (who created/modified what and when)?"
   - "Should there be categories/tags for Projects with their own entities?"

4. DATA CONSISTENCY: Ask about referential integrity:
   - "What happens to Projects when a User is deleted - cascade or orphan?"
   - "Should Sessions automatically expire or require manual cleanup?"
   - "Do we need soft deletes for any entities?"

5. DOMAIN-SPECIFIC RELATIONSHIPS: Based on the specific application:
   - For project management: "Should we add Task/Milestone entities related to Projects?"
   - For collaboration: "Do we need Comment/Activity entities linked to Projects?"
   - For permissions: "Should we add Role/Permission entities with User relationships?"

6. OVERALL SCHEMA VALIDATION: Always include this general question:
   - "Should we add something to the schema or are there any changes you would want to do?"

DO NOT use only generic questions. Generate 4-6 SPECIFIC questions based on actual domain analysis.

Constraints:
- Use evidence precedence: documents > glossary > Figma connectors > UI labels.
- Include sources[] and confidence on every relationship.
- If cardinality is ambiguous, choose a conservative default (one-to-many), lower the confidence, and add an open question.
- Generate SPECIFIC open_questions based on actual analysis of the domain and relationships.
"""
