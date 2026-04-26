#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { renderCup } from "./renderer.js";

const server = new McpServer({
  name: "wirecup",
  version: "1.0.0",
});

server.tool(
  "render",
  "Render wirecup .cup DSL content to HTML wireframe",
  {
    cup: z.string().describe("Wirecup DSL content to render"),
    theme: z.enum(["default", "dark", "clean"]).optional().describe("Theme name"),
  },
  async ({ cup, theme }) => {
    const html = renderCup(cup, theme);
    return { content: [{ type: "text", text: html }] };
  }
);

server.tool(
  "create",
  "Create a wirecup .cup file from a UI description and render it to HTML",
  {
    description: z.string().describe("Description of the UI screen to sketch"),
    cup: z.string().describe("Wirecup DSL content authored by the agent based on the description"),
    theme: z.enum(["default", "dark", "clean"]).optional().describe("Theme name"),
  },
  async ({ cup, theme }) => {
    const html = renderCup(cup, theme);
    return {
      content: [
        { type: "text", text: `<!-- cup -->\n${cup}\n<!-- /cup -->\n\n${html}` },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
