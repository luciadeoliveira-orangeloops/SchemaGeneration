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
  "open_questions":[]
}
Constraints:
- Use camelCase for attribute names.
- Allowed types: string, text, int, bigint, float, decimal(p,s), boolean, date, datetime, uuid, cuid, json, email, url.
- If the type cannot be established, prefer string with lower confidence and add an open question.
"""
