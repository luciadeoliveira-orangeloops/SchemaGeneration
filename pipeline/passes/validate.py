import json
from typing import Dict, Any, Callable
from prompts.system import SYSTEM_PROMPT
from prompts.pass_validate import PASS_VALIDATE

def run_validate(merged_mer: Dict[str, Any], run_model: Callable[[str], str]) -> Dict[str, Any]:
    prompt = (
        SYSTEM_PROMPT
        + "\n\nPASS INSTRUCTIONS:\n"
        + PASS_VALIDATE
        + "\n\nCOMPLETE MER:\n"
        + json.dumps(merged_mer, ensure_ascii=False)
    )
    out = run_model(prompt)
    return json.loads(out)
