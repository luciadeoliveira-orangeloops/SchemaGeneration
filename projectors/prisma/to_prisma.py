from typing import Dict, Any, List
from jinja2 import Template

DEFAULT_TEMPLATE = """// Generated from MER
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

generator client {
  provider = "prisma-client-js"
}

{% for enum in enums %}
enum {{ enum.name }} {
{% for v in enum.values %}
  {{ v | replace("-", "_") | replace(" ", "_") }}
{% endfor %}
}
{% endfor %}

{% for m in models %}
model {{ m.name }} {
{% for a in m.attributes %}
  {{ a.name }} {{ a.type }}{{ "?" if a.nullable else "" }}{{ " @id" if a.pk else "" }}{{ " @unique" if a.unique else "" }}{{ a.default or "" }}
{% endfor %}
{% for r in m.relations %}
  {{ r.field }} {{ r.type }} @relation(fields: [{{ r.fk_field }}], references: [{{ r.ref_field }}])
  {{ r.fk_field }} {{ r.fk_type }}
{% endfor %}
}
{% endfor %}
"""

def map_type(t: str) -> str:
    t = (t or "string").lower()
    return {
        "string":"String",
        "text":"String",
        "int":"Int",
        "bigint":"BigInt",
        "float":"Float",
        "decimal":"Decimal",
        "boolean":"Boolean",
        "date":"DateTime",
        "datetime":"DateTime",
        "uuid":"String",
        "cuid":"String",
        "json":"Json",
        "email":"String",
        "url":"String",
    }.get(t, "String")

def mer_to_prisma(mer: Dict[str, Any]) -> str:
    # Enums
    enums = mer.get("enums", [])

    # Base models
    models = []
    entity_index = {e["name"]: e for e in mer.get("entities", [])}

    # Build base attributes
    for e in mer.get("entities", []):
        attrs = []
        for a in e.get("attributes", []):
            default = ""
            if a.get("default"):
                # Very simple, can be extended with uuid() etc.
                default = f' @default({a["default"]})'
            attrs.append({
                "name": a["name"],
                "type": map_type(a.get("type")),
                "nullable": bool(a.get("nullable")),
                "pk": bool(a.get("pk")),
                "unique": bool(a.get("unique")),
                "default": default,
            })
        models.append({"name": e["name"], "attributes": attrs, "relations": []})

    # Relationships (one-to-many / many-to-one)
    # N:M: for now, expected as explicit bridge table in the MER
    models_by_name = {m["name"]: m for m in models}

    for rel in mer.get("relationships", []):
        typ = rel.get("type", "many-to-one")
        src = rel.get("from"); dst = rel.get("to")
        fk = rel.get("fk", {})
        fk_attr = fk.get("attribute", f"{dst[0].lower()}{dst[1:]}Id")
        ref = fk.get("ref", "id")
        ref_entity, ref_field = (ref.split(".") + ["id"])[:2]

        # FK types
        ref_e = entity_index.get(ref_entity, {})
        ref_attr = next((a for a in ref_e.get("attributes", []) if a.get("name")==ref_field), None)
        fk_type = map_type(ref_attr.get("type") if ref_attr else "string")

        # MANY side (src) → add fk + relation
        if typ in ("many-to-one", "one-to-many"):
            m_src = models_by_name[src]
            m_src["relations"].append({
                "field": dst[0].lower()+dst[1:],  # user
                "type": dst,
                "fk_field": fk_attr,
                "ref_field": ref_field,
                "fk_type": fk_type
            })
            # ONE side (dst) → list
            m_dst = models_by_name[dst]
            # Add list field only if it doesn't exist
            list_field = src[0].lower()+src[1:]+"s"
            if not any(a.get("name")==list_field for a in m_dst["attributes"]):
                m_dst["attributes"].append({
                    "name": list_field,
                    "type": f"{src}[]",
                    "nullable": False,
                    "pk": False,
                    "unique": False,
                    "default": ""
                })

    tmpl = Template(DEFAULT_TEMPLATE)
    return tmpl.render(models=models, enums=enums)
