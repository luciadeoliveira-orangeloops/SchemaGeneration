import os
import sys
import json
from typing import Dict, Any

from pipeline.passes.entities import run_entities
from pipeline.passes.atributes import run_attributes
from pipeline.passes.relationships import run_relationships
from pipeline.passes.validate import run_validate
from pipeline.passes.emit import write_mer

from merge.align import unify_naming
from merge.rules import resolve_cardinality

from validate.schema_validate import validate_mer_basic
from projectors.prisma.to_prisma import mer_to_prisma

from llm.openai_client import run_model  # ← only LLM backend


def load_context(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_parts(e, a, r, ctx) -> Dict[str, Any]:
    # Naive merge of entities and attributes
    entities_by_name: Dict[str, Any] = {x["name"]: x for x in e.get("entities", [])}
    for ea in (a.get("entities") or []):
        name = ea["name"]
        if name in entities_by_name:
            base = entities_by_name[name]
            base["attributes"] = ea.get("attributes", base.get("attributes", []))
            base.setdefault("sources", []).extend(ea.get("sources", []))
            base["confidence"] = max(base.get("confidence", 0), ea.get("confidence", 0))
        else:
            entities_by_name[name] = ea

    relationships = r.get("relationships", [])
    # Apply document rules to cardinalities if they exist
    doc_rules = (ctx.get("documents") or {}).get("rules", [])
    relationships = [resolve_cardinality(rel, doc_rules) for rel in relationships]

    mer = {
        "entities": list(entities_by_name.values()),
        "relationships": relationships,
        "enums": (ctx.get("documents") or {}).get("enums", []),
        "meta": {
            "generation_time": None,
            "open_questions": (
                (e.get("open_questions") or [])
                + (a.get("open_questions") or [])
                + (r.get("open_questions") or [])
            ),
        },
    }
    return mer


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m pipeline.run_all mer <context-pack.json> <out-mer.json>")
        print("  python -m pipeline.run_all prisma <in-mer.json> <out-prisma.schema>")
        print("  python -m pipeline.run_all validate <in-mer.json>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "mer":
        if len(sys.argv) != 4:
            print("Args: mer <context-pack.json> <out-mer.json>")
            sys.exit(2)
        context_path = sys.argv[2]
        out_mer = sys.argv[3]
        ctx = load_context(context_path)

        # Passes with the LLM
        e = run_entities(ctx, run_model)
        a = run_attributes(ctx, e, run_model)
        r = run_relationships(ctx, a, run_model)

        mer = merge_parts(e, a, r, ctx)
        mer = unify_naming(mer, (ctx.get("documents") or {}).get("glossary", []))
        validate_mer_basic(mer)
        write_mer(mer, out_mer)
        print(f"MER generated → {out_mer}")

    elif cmd == "prisma":
        if len(sys.argv) != 4:
            print("Args: prisma <in-mer.json> <out-prisma.schema>")
            sys.exit(2)
        in_mer = sys.argv[2]
        out_prisma = sys.argv[3]
        with open(in_mer, "r", encoding="utf-8") as f:
            mer = json.load(f)
        schema = mer_to_prisma(mer)
        os.makedirs(os.path.dirname(out_prisma), exist_ok=True)
        with open(out_prisma, "w", encoding="utf-8") as f:
            f.write(schema)
        print(f"Prisma schema → {out_prisma}")

    elif cmd == "validate":
        if len(sys.argv) != 3:
            print("Args: validate <in-mer.json>")
            sys.exit(2)
        in_mer = sys.argv[2]
        with open(in_mer, "r", encoding="utf-8") as f:
            mer = json.load(f)
        validate_mer_basic(mer)
        print("MER valid (basic checks).")
    else:
        print("Unrecognized command.")
        sys.exit(2)


if __name__ == "__main__":
    main()