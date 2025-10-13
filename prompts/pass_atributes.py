PASS_ATTRIBUTES = """TASK
For each entity, infer its ATTRIBUTES (type and flags) based on the CONTEXT PACK.

RULES
- Every entity MUST have a primary key (pk = true).
- Mark attributes as derived or view_only when they are computed or presentation-only.
- Add unique when explicitly stated or strongly implied.
- Include sources[] and confidence for each attribute.

OUTPUT (JSON ONLY)
{
  "entities": [
    {
      "name": "User",
      "attributes": [
        {"name":"id","type":"uuid","pk":true,"nullable":false,"sources":["..."],"confidence":0.98},
        {"name":"email","type":"email","unique":true,"nullable":false,"sources":["..."],"confidence":0.90}
      ],
      "sources": ["..."],
      "confidence": 0.90
    }
  ],
  "open_questions":[
    "Based on the documentation analysis, specific questions about attributes"
  ]
}

INSTRUCTIONS FOR OPEN_QUESTIONS:
Analyze the entities and context pack to generate SPECIFIC attribute-related questions:

1. MISSING CRITICAL ATTRIBUTES: Based on the domain and UI, ask about essential fields:
   - "Should User have a 'role' or 'permissions' attribute for access control?"
   - "Does Project need 'status', 'priority', or 'deadline' attributes?"

2. DATA TYPE CONCERNS: When types are ambiguous, ask:
   - "Should 'priority' be an enum (low/medium/high) or integer (1-10)?"
   - "Is 'description' a short string or long text field?"
   - "Should 'createdAt' include timezone information?"

3. BUSINESS RULES: Based on the application context, ask:
   - "Should 'email' be the only login method or also allow 'username'?"
   - "Does 'Project' need financial attributes like 'budget' or 'cost'?"
   - "Should we store 'password' hashed or reference external auth?"

4. UI-DRIVEN ATTRIBUTES: Based on Figma screens, ask:
   - "The login form shows 'Remember me' - should User have 'rememberToken'?"
   - "Project list shows dates - do we need 'updatedAt' or just 'createdAt'?"
   - "Should we store UI preferences like 'theme' or 'language'?"

5. VALIDATION & CONSTRAINTS: Ask about data integrity:
   - "What's the minimum/maximum length for project names?"
   - "Should 'email' validation be strict or allow plus addressing?"
   - "Are there any attributes that should be immutable after creation?"

DO NOT use generic questions. Generate 3-5 SPECIFIC questions based on the actual entities and context.

Constraints:
- Use camelCase for attribute names.
- Allowed types: string, text, int, bigint, float, decimal(p,s), boolean, date, datetime, uuid, cuid, json, email, url.
- If the type cannot be established, prefer string with lower confidence and add an open question.
- Generate SPECIFIC open_questions based on actual analysis of entities and context pack.
"""
