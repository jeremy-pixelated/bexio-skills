# bexio-skills

Claude skills for working with Bexio accounting through an MCP connector that exposes `bexio_*` tools.

- `bexio`: core skill, load first. Routes the request and runs the confirmation gate.
- 9 segment skills: contacts, sales, purchase, accounting, banking, items, projects, files, admin. Each ships a generated per-operation reference from the official Bexio OpenAPI spec.
- Gated actions (send, delete, cancel, payment order, posting): one preview, one explicit yes, then execute.
- `plugins/bexio/freigaben/`: human-readable overview of which actions run directly and which need a yes (German).

The skills contain no credentials, no addresses and no connector code. They work with a Bexio MCP connector that exposes the `bexio_*` tools they reference.

**Connector requirement for gated actions.** The preview step calls the write with `dry_run: true` and expects the connector to write nothing and return `status: "dry_run"`; the yes step passes `acknowledge_flags`. Both must be declared in the write tool's input schema. The core skill checks this and treats gated actions as unavailable on a connector without `dry_run`. Do not remove that check: a connector that ignores unknown arguments would execute the "preview" for real.

## Install

Claude Code:

```
/plugin marketplace add jeremy-pixelated/bexio-skills
/plugin install bexio@bexio-skills
```

Claude app (Cowork): add this repository as a plugin marketplace, then install the `bexio` plugin.

Update: pull the marketplace again, then update the plugin.

## Disclaimer

Independent project, not affiliated with or endorsed by bexio AG. "Bexio" is a trademark of its owner.
