#!/usr/bin/env python3
"""gen_reference.py: writes one reference.md per bexio segment skill from the official spec.

Source of truth: the OpenAPI 3.0.2 spec embedded in https://docs.bexio.com/
(`__redoc_state.spec.data`). One telegraph row per operation of the tags a segment owns:
operationId (doc anchor link) | summary | METHOD path | MCP tool.action | gate |
required body/query fields | enums | scopes. Stdlib only.

MCP mapping: op-map.json (next to this script): operationId -> connector tool.action.
Missing op-map entry
-> tool column `—` (not reachable).

Usage:
  python3 gen_reference.py <bexio-openapi.json> [--op-map op-map.json]
                           [--skills-dir ../..] [--fetched YYYY-MM-DD] [--check]
--check: write nothing, exit 1 if any reference.md differs from what would be generated.
"""
import argparse
import hashlib
import json
import os
import sys

# Router: API tag -> owning skill. Mirrors the router table in skills/bexio/SKILL.md.
# Every tag in the spec must appear here (the script aborts otherwise).
TAG_SKILL = {
    "Contacts": "bexio-contacts", "Contact Relations": "bexio-contacts",
    "Contact Groups": "bexio-contacts", "Contact Sectors": "bexio-contacts",
    "Additional Addresses": "bexio-contacts",
    "Quotes": "bexio-sales", "Orders": "bexio-sales", "Deliveries": "bexio-sales",
    "Invoices": "bexio-sales", "Document Settings": "bexio-sales",
    "Document templates": "bexio-sales", "Comments": "bexio-sales",
    "Default positions": "bexio-sales", "Item positions": "bexio-sales",
    "Text positions": "bexio-sales", "Subtotal positions": "bexio-sales",
    "Discount positions": "bexio-sales", "Pagebreak positions": "bexio-sales",
    "Sub positions": "bexio-sales",
    "Bills": "bexio-purchase", "Expenses": "bexio-purchase",
    "Purchase Orders": "bexio-purchase", "Outgoing Payment": "bexio-purchase",
    "Accounts": "bexio-accounting", "Account Groups": "bexio-accounting",
    "Calendar Years": "bexio-accounting", "Business Years": "bexio-accounting",
    "Currencies": "bexio-accounting", "Manual Entries": "bexio-accounting",
    "Reports": "bexio-accounting", "Taxes": "bexio-accounting",
    "Vat Periods": "bexio-accounting",
    "Bank Accounts": "bexio-banking", "Payments": "bexio-banking",
    "Items": "bexio-items", "Stock locations": "bexio-items", "Stock Areas": "bexio-items",
    "Projects": "bexio-projects", "Timesheets": "bexio-projects",
    "Business Activities": "bexio-projects",
    "Files": "bexio-files",
    "User Management": "bexio-admin", "Permissions": "bexio-admin", "Notes": "bexio-admin",
    "Tasks": "bexio-admin", "Company Profile": "bexio-admin", "Countries": "bexio-admin",
    "Languages": "bexio-admin", "Payment Types": "bexio-admin", "Units": "bexio-admin",
    "Salutations": "bexio-admin", "Titles": "bexio-admin",
    "Communication Types": "bexio-admin",
    "Employees": None, "Absences": None, "Documents": None,  # payroll: not covered
}
# Connector overrides: fields the connector's tool schema requires although the spec does not.
# Rendered in the `required` column as "connector requires: <fields>". Keyed by operationId.
CONNECTOR_REQUIRED = {
    # spec requires only `value`; the tool schema also requires `date`
    # (matches skills/bexio-sales/SKILL.md "Payments received").
    "v2CreateInvoicePayment": ["date"],
}
# Payload-dependent gates (skills/bexio/SKILL.md §3.1 "Also gated"): tool.action -> extra gate label.
CONDITIONAL_GATE = {
    "bexio_bills.create": "**OK** payment order with `payment`",
    "bexio_bills.update": "**OK** payment order with `payment`",
}
METHODS = ("get", "post", "put", "patch", "delete")
ENUM_MAX = 14


def canon_sha256(spec):
    """sha256 over the canonical JSON of the spec without x-codeSamples (stable across fetches)."""
    def strip(x):
        if isinstance(x, dict):
            return {k: strip(v) for k, v in x.items() if k != "x-codeSamples"}
        if isinstance(x, list):
            return [strip(v) for v in x]
        return x
    raw = json.dumps(strip(spec), sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Resolver:
    def __init__(self, spec):
        self.spec = spec

    def ref(self, node, depth=0):
        while isinstance(node, dict) and "$ref" in node and depth < 20:
            parts = node["$ref"].lstrip("#/").split("/")
            cur = self.spec
            for p in parts:
                cur = cur[p.replace("~1", "/").replace("~0", "~")]
            node, depth = cur, depth + 1
        return node

    def merged(self, schema, depth=0):
        """Flatten allOf; returns (properties, required, variants) for an object schema."""
        schema = self.ref(schema)
        if not isinstance(schema, dict) or depth > 6:
            return {}, [], []
        props, req, variants = dict(schema.get("properties", {})), list(schema.get("required", [])), []
        for sub in schema.get("allOf", []):
            p, r, v = self.merged(sub, depth + 1)
            props.update(p)
            req += [x for x in r if x not in req]
            variants += v
        for key in ("oneOf", "anyOf"):
            if schema.get(key):
                variants.append([self.ref(s) for s in schema[key]])
        return props, req, variants


def enum_of(r, schema):
    s = r.ref(schema)
    if not isinstance(s, dict):
        return None
    if "enum" in s:
        return s["enum"]
    if s.get("type") == "array" and isinstance(r.ref(s.get("items")), dict) and "enum" in r.ref(s.get("items")):
        return r.ref(s["items"])["enum"]
    return None


def fmt_enum(name, values):
    vals = [("null" if v is None else str(v)) for v in values]
    if len(vals) > ENUM_MAX:
        vals = vals[:ENUM_MAX] + ["…(+%d)" % (len(values) - ENUM_MAX)]
    return "`%s`∈%s" % (name, "|".join(vals))


def required_fields(r, schema, depth=0):
    """Telegraph list of required fields: a, b{c,d}, e[]{f}; oneOf variants joined by ' / '."""
    s = r.ref(schema)
    if not isinstance(s, dict):
        return ""
    if s.get("type") == "array":
        inner = required_fields(r, s.get("items", {}), depth)
        return "[]{%s}" % inner if inner else "[]"
    props, req, variants = r.merged(s)
    out = []
    for name in req:
        sub = r.ref(props.get(name, {}))
        tail = ""
        if depth < 1 and isinstance(sub, dict):
            if sub.get("type") == "array":
                inner = required_fields(r, sub.get("items", {}), depth + 1)
                tail = "[]{%s}" % inner if inner else "[]"
            else:
                sp, sr, _ = r.merged(sub)
                if sr:
                    tail = "{%s}" % ",".join(sr)
        out.append(name + tail)
    text = ", ".join(out)
    if variants and not req:
        alts = []
        for group in variants:
            if len(group) == 1:  # single-variant wrapper: its own required list
                inner = required_fields(r, group[0], depth)
                if inner:
                    alts.append(inner)
                continue
            names = []
            for v in group:
                title = v.get("title") or ""
                vr = required_fields(r, v, depth + 1) if depth < 1 else ""
                names.append((title + ":" if title else "") + (vr or "–"))
            if any(n not in ("–",) and not n.endswith(":–") for n in names):
                alts.append("one of: " + " / ".join(names))
        text = " ; ".join(alts)
    return text


def body_schema(r, op):
    rb = r.ref(op.get("requestBody"))
    if not isinstance(rb, dict):
        return None, None
    content = rb.get("content", {})
    for ctype in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded"):
        if ctype in content:
            return ctype, content[ctype].get("schema", {})
    for ctype, c in content.items():
        return ctype, c.get("schema", {})
    return None, None


def collect_enums(r, op, params):
    found = []
    seen = set()

    def add(name, values):
        key = (name, tuple(map(str, values)))
        if key not in seen:
            seen.add(key)
            found.append(fmt_enum(name, values))

    for p in params:
        if p.get("in") in ("query", "path"):
            e = enum_of(r, p.get("schema", {}))
            if e:
                add(p["name"], e)
    _, bs = body_schema(r, op)
    if bs is not None:
        s = r.ref(bs)
        if isinstance(s, dict) and s.get("type") == "array":
            s = r.ref(s.get("items", {}))
        props, _, variants = r.merged(s)
        for group in variants:
            for v in group:
                vp, _, _ = r.merged(v)
                props = {**vp, **props}
        for name, sub in props.items():
            e = enum_of(r, sub)
            if e:
                add(name, e)
            sub_r = r.ref(sub)
            if isinstance(sub_r, dict):
                target = r.ref(sub_r.get("items", {})) if sub_r.get("type") == "array" else sub_r
                sp, _, _ = r.merged(target)
                for n2, s2 in sp.items():
                    e2 = enum_of(r, s2)
                    if e2:
                        add("%s.%s" % (name, n2), e2)
    # response: status-like enums (what the object can be in)
    for code in ("200", "201"):
        resp = r.ref(op.get("responses", {}).get(code, {}))
        sch = (resp.get("content", {}).get("application/json", {}) or {}).get("schema") if isinstance(resp, dict) else None
        if sch is None:
            continue
        s = r.ref(sch)
        if isinstance(s, dict) and s.get("type") == "array":
            s = r.ref(s.get("items", {}))
        props, _, _ = r.merged(s)
        if "data" in props and not any("status" in k for k in props):
            d = r.ref(props["data"])
            if isinstance(d, dict) and d.get("type") == "array":
                d = r.ref(d.get("items", {}))
            props, _, _ = r.merged(d)
        for name, sub in props.items():
            if "status" in name or name in ("type", "locked_info"):
                e = enum_of(r, sub)
                if e:
                    add("→" + name, e)
    return found


def scopes_of(op, spec):
    sec = op.get("security", spec.get("security", []))
    names = []
    for alt in sec:
        for _scheme, scopes in alt.items():
            for s in scopes:
                if s not in names:
                    names.append(s)
    return names


def gate_of(tool_meta, tool, action):
    meta = tool_meta.get(tool, {})
    if action in meta.get("confirm", []):
        if action == "send":
            cls = "send"
        elif action == "cancel":
            cls = "cancel"
        elif action in meta.get("destructive", []):
            cls = "delete"
        elif tool in ("bexio_banking_payments", "bexio_outgoing_payments"):
            cls = "payment order"
        else:
            cls = "posting"
        return "**OK** %s" % cls
    if action in meta.get("write", []):
        return "write"
    return "read"


def slug(tag):
    return tag.replace(" ", "-")


def esc(text):
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def build(spec, opmap, fetched):
    r = Resolver(spec)
    tool_meta = opmap.get("tools", {})
    ops_map = opmap.get("ops", {})
    by_skill = {}
    tag_order = []
    missing_tags = set()
    for path, item in spec["paths"].items():
        shared = item.get("parameters", [])
        for meth in METHODS:
            op = item.get(meth)
            if not op:
                continue
            tag = op["tags"][0]
            if tag not in TAG_SKILL:
                missing_tags.add(tag)
                continue
            skill = TAG_SKILL[tag]
            if skill is None:
                continue
            if tag not in tag_order:
                tag_order.append(tag)
            params = [r.ref(p) for p in shared + op.get("parameters", [])]
            req_q = [p["name"] for p in params if p.get("in") == "query" and p.get("required")]
            ctype, bs = body_schema(r, op)
            req_body = required_fields(r, bs) if bs is not None else ""
            req = []
            if req_body:
                req.append(req_body)
            if ctype and ctype != "application/json":
                req.append("(%s)" % ctype.split("/")[-1])
            if req_q:
                req.append("q: " + ", ".join(req_q))
            if op["operationId"] in CONNECTOR_REQUIRED:
                req.append("connector requires: " + ", ".join(CONNECTOR_REQUIRED[op["operationId"]]))
            mapped = ops_map.get(op["operationId"], [])
            tools = []
            gates = []
            for ta in mapped:
                tool, _, action = ta.partition(".")
                action = action.split("[")[0]
                tools.append("`%s`" % ta)
                g = gate_of(tool_meta, tool, action)
                if "%s.%s" % (tool, action) in CONDITIONAL_GATE:
                    g += "; " + CONDITIONAL_GATE["%s.%s" % (tool, action)]
                if g not in gates:
                    gates.append(g)
            dep = " *(deprecated)*" if op.get("deprecated") else ""
            row = "| [%s](https://docs.bexio.com/#tag/%s/operation/%s)%s | %s | `%s %s` | %s | %s | %s | %s | %s |" % (
                op["operationId"], slug(tag), op["operationId"], dep, esc(op.get("summary")),
                meth.upper(), path, ", ".join(tools) or "—", ", ".join(gates) or "—",
                esc("; ".join(req)) or "–", esc(" · ".join(collect_enums(r, op, params))) or "–",
                esc(" ".join(scopes_of(op, spec))) or "–")
            by_skill.setdefault(skill, {}).setdefault(tag, []).append(row)
    if missing_tags:
        sys.exit("unmapped tags (add to TAG_SKILL): %s" % sorted(missing_tags))
    known_ops = {op.get("operationId") for item in spec["paths"].values() for m in METHODS if (op := item.get(m))}
    stale = sorted(set(CONNECTOR_REQUIRED) - known_ops)
    if stale:
        sys.exit("CONNECTOR_REQUIRED names operationIds not in the spec: %s" % stale)
    sha = canon_sha256(spec)
    files = {}
    for skill, tags in by_skill.items():
        n = sum(len(v) for v in tags.values())
        lines = [
            "# %s — operation reference (generated)" % skill,
            "",
            "GENERATED by `skills/bexio/tools/gen_reference.py` — do not edit by hand; re-run the script.",
            "Source: https://docs.bexio.com/ OpenAPI %s (info.version %s), fetched %s, spec sha256 `%s` (canonical JSON, x-codeSamples stripped). MCP mapping: `skills/bexio/tools/op-map.json` (operationId → connector tool.action)."
            % (spec.get("openapi"), spec.get("info", {}).get("version"), fetched, sha),
            "",
            "Legend: gate `**OK** <class>` = dry run + one preview + one yes (core §3) · `write` = do + report id · `read` = no gate · tool `—` = not reachable via MCP · required: `a{b,c}` nested, `x[]{y}` array items, `q:` required query · `→field` = enum in the response · scopes = API scopes the op declares.",
            "",
            "%d operations, %d tags." % (n, len(tags)),
            "",
        ]
        for tag in [t for t in TAG_SKILL if t in tags]:
            rows = tags[tag]
            lines += [
                "## %s (%d)" % (tag, len(rows)),
                "",
                "| operationId | summary | METHOD path | MCP tool.action | gate | required | enums | scopes |",
                "|---|---|---|---|---|---|---|---|",
            ] + rows + [""]
        files[skill] = "\n".join(lines)
    return files


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--op-map", default=os.path.join(here, "op-map.json"))
    ap.add_argument("--skills-dir", default=os.path.normpath(os.path.join(here, "..", "..")))
    ap.add_argument("--fetched", default="2026-09-24")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    with open(a.spec, encoding="utf-8") as f:
        spec = json.load(f)
    if "spec" in spec and "data" in spec.get("spec", {}):
        spec = spec["spec"]["data"]
    with open(a.op_map, encoding="utf-8") as f:
        opmap = json.load(f)
    files = build(spec, opmap, a.fetched)
    drift = 0
    for skill, text in sorted(files.items()):
        path = os.path.join(a.skills_dir, skill, "reference.md")
        if a.check:
            old = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            if old != text:
                drift += 1
                print("DRIFT", path)
            continue
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote %s (%d lines)" % (path, text.count("\n") + 1))
    print("spec sha256 (canonical, no x-codeSamples): %s" % canon_sha256(spec))
    if a.check and drift:
        sys.exit(1)


if __name__ == "__main__":
    main()
