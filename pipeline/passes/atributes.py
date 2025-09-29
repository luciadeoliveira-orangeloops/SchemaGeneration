import json
from typing import Dict, Any, Callable
from prompts.system import SYSTEM_PROMPT
from prompts.pass_atributes import PASS_ATTRIBUTES

def run_attributes(context_pack: Dict[str, Any], base_mer: Dict[str, Any], run_model: Callable[[str], str]) -> Dict[str, Any]:
    print("🔄 [ATTRIBUTES] Building attributes pass prompt...")
    prompt = (
        SYSTEM_PROMPT
        + "\n\nPASS INSTRUCTIONS:\n"
        + PASS_ATTRIBUTES
        + "\n\nPARTIAL MER (ENTITIES):\n"
        + json.dumps(base_mer, ensure_ascii=False)
        + "\n\nCONTEXT PACK:\n"
        + json.dumps(context_pack, ensure_ascii=False)
    )
    print(f"🔄 [ATTRIBUTES] Prompt built, calling LLM...")
    out = run_model(prompt)
    print(f"🔄 [ATTRIBUTES] LLM response received, parsing JSON...")
    result = json.loads(out)
    print(f"🔄 [ATTRIBUTES] Attributes pass completed successfully")
    return result
