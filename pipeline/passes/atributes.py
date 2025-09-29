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
    
    # Handle empty responses from LLM
    if not out or out.strip() == "":
        print(f"⚠️ [ATTRIBUTES] Empty response from LLM, retrying...")
        out = run_model(prompt)
        print(f"🔄 [ATTRIBUTES] Retry response received, parsing JSON...")
    
    if not out or out.strip() == "":
        print(f"❌ [ATTRIBUTES] LLM returned empty response after retry, using fallback...")
        # Return a fallback structure with entities from context
        entities = base_mer.get("entities", [])
        return {
            "entities": entities,
            "open_questions": [
                {
                    "question": "LLM returned empty response for attributes. Please review and add attributes manually.",
                    "sources": ["system:llm_error"]
                }
            ]
        }
    
    try:
        result = json.loads(out)
        print(f"🔄 [ATTRIBUTES] Attributes pass completed successfully")
        return result
    except json.JSONDecodeError as e:
        print(f"❌ [ATTRIBUTES] JSON parsing error: {e}")
        print(f"🔄 [ATTRIBUTES] LLM response was: {out[:200]}...")
        # Return fallback structure
        entities = base_mer.get("entities", [])
        return {
            "entities": entities,
            "open_questions": [
                {
                    "question": f"LLM response parsing failed: {e}. Please review and add attributes manually.",
                    "sources": ["system:json_error"]
                }
            ]
        }
