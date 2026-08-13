#!/usr/bin/env node

// Wirecup MCP server.
//
// The agent writes .cup source. The wirecup server renders it.
// No HTML crosses this boundary, so tool results stay small.
//
// Reading, listing and deleting mocks is not here on purpose. The agent
// already has file tools. This server only adds what those cannot do:
// the spec in one block, and a check against the real parser before saving.

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const ROOT = path.resolve(process.env.WIRECUP_ROOT || process.cwd());
const BASE = `http://localhost:${process.env.WIRECUP_PORT || 8765}`;

const SPEC = `Wirecup: one character starts a line and picks the element. The rest is content.

n nav       h heading    t text      i input     b button
x image     s select     l list      v badge     a alert
k checkbox  u include    c card      r row       g grid
-  thin rule            =  thick rule

Links: "b Label|target", same for nav items. "target" or "target.cup" becomes a
route. "http..." and "/path" stay as written. No "|target" means no link.
Nav items and grid cells split on 2 or more spaces, so a label can hold single spaces.
c, r and g take indented children. Indentation makes the structure.
g: the g line is the header row. Indented lines below it are data rows, not elements.
   A cell may start with v, b, s, i or k to put that element in the cell.
   Short rows are padded out to the header width.
Consecutive l lines become one list.
Includes: put snippets in .wirecup/_includes/name.cup, call "u name arg1", use $1 $2 $*.
Badges and alerts are neutral. Colour carries no meaning.
An unknown first character is an error.`;

const text = (s: string) => ({ content: [{ type: "text" as const, text: s }] });

const server = new McpServer({ name: "wirecup", version: "2.0.0" });

server.tool("spec", "The whole Wirecup DSL in one short block. Read this before writing a mock.", {}, async () =>
  text(SPEC)
);

server.tool(
  "write",
  "Save a mock to .wirecup/<name>.cup and return its preview URL. " +
    "The wirecup server renders it; no HTML comes back through this tool.",
  {
    name: z.string().describe("Mock name, without the .cup suffix"),
    cup: z.string().describe("Wirecup DSL source. Call the spec tool if unsure."),
  },
  async ({ name, cup }) => {
    const id = name.trim().replace(/\.cup$/, "");
    if (!/^[\w-]+$/.test(id)) return text(`Bad name '${name}'. Use letters, digits, - and _.`);

    // Check with the running server, so there is only ever one parser.
    let note = "";
    try {
      const r = await fetch(`${BASE}/api/validate`, { method: "POST", body: cup, signal: AbortSignal.timeout(2000) });
      const errors = ((await r.json()) as { errors: string[] }).errors;
      if (errors.length) return text(`Not saved. ${errors.length} error(s):\n${errors.join("\n")}`);
    } catch {
      note = `\nNot checked: no wirecup server on ${BASE}. Start one from WirecupBar or with: wirecup ${ROOT}`;
    }

    const file = path.join(ROOT, ".wirecup", `${id}.cup`);
    await mkdir(path.dirname(file), { recursive: true });
    await writeFile(file, cup.endsWith("\n") ? cup : `${cup}\n`, "utf8");
    return text(`ok  ${file}\n${BASE}/__wirecup?file=${id}.cup${note}`);
  }
);

await server.connect(new StdioServerTransport());
