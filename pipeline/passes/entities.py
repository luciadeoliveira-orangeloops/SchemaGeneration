import json
from typing import Dict, Any, Callable
from prompts.system import SYSTEM_PROMPT
from prompts.pass_entities import PASS_ENTITIES

def run_entities(context_pack: Dict[str, Any], run_model: Callable[[str], str]) -> Dict[str, Any]:
    print("🔄 [ENTITIES] Building entities pass prompt...")
    prompt = (
        SYSTEM_PROMPT
        + "\n\nPASS INSTRUCTIONS:\n"
        + PASS_ENTITIES
        + "\n\nCONTEXT PACK:\n"
        + json.dumps(context_pack, ensure_ascii=False)
    )
    print(f"🔄 [ENTITIES] Prompt built, calling LLM...")
    out = run_model(prompt)
    print(f"🔄 [ENTITIES] LLM response received, parsing JSON...")
    result = json.loads(out)
    print(f"🔄 [ENTITIES] Entities pass completed successfully")
    return result
