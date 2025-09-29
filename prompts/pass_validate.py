PASS_VALIDATE = """TASK
Validate the final MER: primary keys, resolved foreign keys, unique names, and type sanity. Suggest indexes when appropriate.

OUTPUT (JSON ONLY)
{
  "status": "ok" | "warnings" | "errors",
  "issues": [
    {"level":"warning","code":"MISSING_INDEX","message":"Consider adding an index on User.email","sources":["..."]},
    {"level":"error","code":"MISSING_PK","message":"Entity Order has no primary key","sources":["..."]}
  ]
}
Constraints:
- Do not modify the MER here; only report validation issues and suggestions.
- Prefer precise, short messages with clear references in sources[].
"""
