import json
from typing import Dict, Any, Callable
from prompts.system import SYSTEM_PROMPT
from prompts.pass_relationships import PASS_RELATIONSHIPS

def run_relationships(context_pack: Dict[str, Any], base_mer: Dict[str, Any], run_model: Callable[[str], str]) -> Dict[str, Any]:
    print("🔄 [RELATIONSHIPS] Building relationships pass prompt...")
    prompt = (
        SYSTEM_PROMPT
        + "\n\nPASS INSTRUCTIONS:\n"
        + PASS_RELATIONSHIPS
        + "\n\nPARTIAL MER (ENTITIES+ATTRIBUTES):\n"
        + json.dumps(base_mer, ensure_ascii=False)
        + "\n\nCONTEXT PACK:\n"
        + json.dumps(context_pack, ensure_ascii=False)
    )
    print(f"🔄 [RELATIONSHIPS] Prompt built, calling LLM...")
    out = run_model(prompt)
    print(f"🔄 [RELATIONSHIPS] LLM response received, parsing JSON...")
    result = json.loads(out)
    print(f"🔄 [RELATIONSHIPS] Relationships pass completed successfully")
    return result
