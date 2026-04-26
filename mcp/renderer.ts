// Wirecup renderer — ported from wirecup-render.py

interface Theme {
  fonts: { primary: string; fallback: string; google_url: string };
  colors: Record<string, string>;
  sketchy: { page_rotation: number; card_rotation: number; card_rotation_alt: number; divider_rotation: number };
  layout: Record<string, string>;
}

const DEFAULT_THEME: Theme = {
  fonts: {
    primary: "Kalam",
    fallback: "Comic Sans MS, cursive, sans-serif",
    google_url: "https://fonts.googleapis.com/css2?family=Kalam:wght@300;400;700&display=swap",
  },
  colors: {
    bg_page: "#f5f5f0", bg_card: "#fffef8", bg_input: "#fafafa", bg_button: "#eee",
    bg_image: "#e8e8e8", bg_badge_green: "#e6f4ea", bg_badge_amber: "#fef3e8",
    bg_badge_red: "#fce8e8", bg_badge_blue: "#e8f0fe", bg_badge_grey: "#f1f3f4",
    bg_alert_green: "#e6f4ea", bg_alert_amber: "#fef3e8", bg_alert_red: "#fce8e8",
    bg_alert_blue: "#e8f0fe", bg_table_header: "#f0f0e8", bg_table_alt: "#fafaf5",
    text_primary: "#333", text_secondary: "#555", text_muted: "#999", text_placeholder: "#bbb",
    text_badge_green: "#137333", text_badge_amber: "#b06000", text_badge_red: "#a50e0e",
    text_badge_blue: "#174ea6", text_badge_grey: "#5f6368",
    text_alert_green: "#137333", text_alert_amber: "#b06000", text_alert_red: "#a50e0e",
    text_alert_blue: "#174ea6",
    border_page: "#ccc", border_light: "#aaa", border_medium: "#888", border_dark: "#555",
    border_card: "#777", border_image: "#aaa",
    border_badge_green: "#34a853", border_badge_amber: "#f9ab00", border_badge_red: "#ea4335",
    border_badge_blue: "#4285f4", border_badge_grey: "#9aa0a6",
    border_alert_green: "#34a853", border_alert_amber: "#f9ab00", border_alert_red: "#ea4335",
    border_alert_blue: "#4285f4", border_checkbox: "#666",
    shadow: "rgba(0,0,0,0.1)", shadow_button: "#bbb",
  },
  sketchy: { page_rotation: -0.3, card_rotation: 0.2, card_rotation_alt: -0.1, divider_rotation: -0.1 },
  layout: {
    page_width: "900px", page_padding: "30px", card_padding: "14px", card_margin: "10px 0",
    card_radius: "6px", button_padding: "8px 18px", button_radius: "6px",
    input_padding: "8px 10px", input_radius: "4px", image_min_height: "80px",
    image_border: "dashed", alert_padding: "12px 16px", alert_radius: "6px",
    badge_padding: "3px 10px", badge_radius: "12px", table_padding: "8px 12px",
  },
};

function buildCss(theme: Theme): string {
  const vars = Object.entries(theme.colors).map(([k, v]) => `  --${k}: ${v};`).join("\n");
  const layout = Object.entries(theme.layout).map(([k, v]) => `  --${k}: ${v};`).join("\n");
  const { primary, fallback, google_url } = theme.fonts;
  const s = theme.sketchy;
  return `
<script src="https://cdn.tailwindcss.com"></script>
<style>
@import url('${google_url}');
:root {
${vars}
${layout}
}
body { font-family: '${primary}', ${fallback}; background: var(--bg_page); }
.sketchy-page { transform: rotate(${s.page_rotation}deg); }
.sketchy-card { transform: rotate(${s.card_rotation}deg); }
.sketchy-card-alt { transform: rotate(${s.card_rotation_alt}deg); }
.sketchy-divider { transform: rotate(${s.divider_rotation}deg); }
</style>`;
}

function pageWrap(theme: Theme, inner: string): string {
  return `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
${buildCss(theme)}
</head>
<body class="min-h-screen p-8 md:p-12">
<div class="page mx-auto bg-[var(--bg-card)] p-[var(--page-padding)] border-2 border-[var(--border-page)] shadow-lg max-w-[var(--page-width)] sketchy-page">
${inner}
</div>
</body>
</html>`;
}

function parseLink(content: string): [string, string] {
  if (!content.includes("|")) return [content.trim(), ""];
  const [label, target] = content.split("|", 2);
  let href = target.trim();
  if (!href.startsWith("http")) {
    if (href.endsWith(".cup")) href = href.slice(0, -4) + ".html";
    else if (!href.includes(".")) href = href + ".html";
  }
  return [label.trim(), href];
}

function elNav(content: string): string {
  const items = content.split(/\s+/).filter(Boolean).map((x) => {
    const [label, href] = parseLink(x);
    return href
      ? `<a href="${href}" class="hover:underline text-[var(--text-primary)]">${label}</a>`
      : `<span class="hover:underline cursor-default text-[var(--text-primary)]">${label}</span>`;
  });
  return `<nav class="flex gap-6 pb-2 mb-4 border-b-2 border-[var(--border-medium)] text-[0.95em]">${items.join("")}</nav>`;
}

function elHeading(content: string): string {
  return `<h2 class="text-[1.6em] font-bold my-3 tracking-tight text-[var(--text-primary)]">${content}</h2>`;
}

function elText(content: string): string {
  return `<p class="my-1.5 text-[0.95em] text-[var(--text-secondary)]">${content}</p>`;
}

function elInput(content: string): string {
  const placeholder = content.trim() || "________";
  return `<div class="inline-block min-w-[200px] my-1.5 p-[var(--input-padding)] border-2 border-[var(--border-medium)] rounded-[var(--input-radius)] bg-[var(--bg-input)] text-[var(--text-placeholder)] italic">${placeholder}</div>`;
}

function elButton(content: string): string {
  const [label, href] = parseLink(content);
  const text = label || "OK";
  const cls = "inline-block my-2 px-[18px] py-[8px] border-2 border-[var(--border-dark)] rounded-[var(--button-radius)] bg-[var(--bg-button)] cursor-default shadow-[1px_2px_0_var(--shadow-button)] text-[var(--text-primary)] no-underline";
  return href ? `<a href="${href}" class="${cls}">${text}</a>` : `<button class="${cls}">${text}</button>`;
}

function elImage(content: string): string {
  const label = content.trim() || "img";
  return `<div class="flex items-center justify-center my-1.5 min-h-[var(--image-min-height)] min-w-[80px] bg-[var(--bg-image)] border-2 border-[var(--border-image)] text-[var(--text-muted)] text-[0.8em]" style="border-style:dashed">${label}</div>`;
}

function elSelect(content: string): string {
  const label = content.trim() || "...";
  return `<div class="relative inline-block my-1.5 pr-7 pl-2.5 py-[8px] border-2 border-[var(--border-medium)] rounded-[var(--input-radius)] bg-[var(--bg-input)]">${label}<span class="absolute right-2 top-1/2 -translate-y-1/2">▾</span></div>`;
}

function elList(content: string): string {
  return `<li class="my-1 pl-4 list-disc text-[var(--text-primary)]">${content}</li>`;
}

function elDivider(thick = false): string {
  const w = thick ? "3px" : "2px";
  const c = thick ? "var(--border-card)" : "var(--border-light)";
  return `<hr class="my-3 border-0 border-t-[${w}] border-[${c}] sketchy-divider">`;
}

function elBadge(content: string): string {
  const text = content.trim().toLowerCase();
  const map: Record<string, string[]> = {
    green: "approved confirmed active free available success yes green".split(" "),
    amber: "pending review warning amber yellow wait".split(" "),
    red: "rejected error blocked red no unavailable withdrawn".split(" "),
    blue: "info blue new updated note".split(" "),
  };
  let color = "grey";
  for (const [c, words] of Object.entries(map)) {
    if (words.includes(text)) { color = c; break; }
  }
  return `<span class="inline-block my-0.5 mx-1 px-[10px] py-[3px] text-[0.8em] font-bold rounded-[var(--badge-radius)] border-2 bg-[var(--bg_badge_${color})] border-[var(--border_badge_${color})] text-[var(--text_badge_${color})]">${content.trim()}</span>`;
}

function elAlert(content: string): string {
  const text = content.trim().toLowerCase();
  let color = "blue";
  if (/success|confirmed|approved|green/.test(text)) color = "green";
  else if (/warning|pending|review|amber|attention/.test(text)) color = "amber";
  else if (/error|rejected|failed|red|urgent/.test(text)) color = "red";
  return `<div class="my-2.5 p-[var(--alert-padding)] rounded-[var(--alert-radius)] border-2 text-[0.95em] bg-[var(--bg_alert_${color})] border-[var(--border_alert_${color})] text-[var(--text_alert_${color})]">${content.trim()}</div>`;
}

function elCheckbox(content: string): string {
  return `<label class="flex items-center gap-2 my-1.5 text-[0.95em] text-[var(--text-primary)]"><span class="inline-block w-[18px] h-[18px] border-2 border-[var(--border-checkbox)] rounded-[3px] shrink-0"></span><span>${content.trim()}</span></label>`;
}

function splitCells(line: string): string[] {
  return line.trim().split(/  +/).map((s) => s.trim()).filter(Boolean);
}

function renderTable(headerLine: string, rows: string[]): string {
  const headers = splitCells(headerLine);
  const headerHtml = headers.map((h) => `<th class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] text-left bg-[var(--bg_table_header)] font-bold">${h}</th>`).join("");
  const rowsHtml = rows.map((row, idx) => {
    const bg = idx % 2 ? "bg-[var(--bg_table_alt)]" : "";
    const cells = splitCells(row).map((cell) => {
      if (cell.startsWith("v ")) return `<td class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] ${bg}">${elBadge(cell.slice(2))}</td>`;
      if (cell.startsWith("b ")) return `<td class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] ${bg}">${elButton(cell.slice(2))}</td>`;
      return `<td class="p-[var(--table-padding)] border-2 border-[var(--border-medium)] ${bg}">${cell}</td>`;
    }).join("");
    return `<tr>${cells}</tr>`;
  }).join("");
  return `<div class="my-2.5 overflow-x-auto"><table class="w-full border-collapse text-[0.9em]"><thead><tr>${headerHtml}</tr></thead><tbody>${rowsHtml}</tbody></table></div>`;
}

function indentLevel(line: string): number {
  return line.length - line.trimStart().length;
}

function renderLines(lines: string[], startIdx = 0): [string, number] {
  const parts: string[] = [];
  let i = startIdx;
  while (i < lines.length) {
    const raw = lines[i++];
    const stripped = raw.trimStart();
    if (!stripped) continue;
    const lv = indentLevel(raw);
    const typ = stripped[0];
    const content = stripped.slice(1).trimStart();

    if (typ === "n") { parts.push(elNav(content)); continue; }
    if (typ === "h") { parts.push(elHeading(content)); continue; }
    if (typ === "t") { parts.push(elText(content)); continue; }
    if (typ === "i") { parts.push(elInput(content)); continue; }
    if (typ === "b") { parts.push(elButton(content)); continue; }
    if (typ === "x") { parts.push(elImage(content)); continue; }
    if (typ === "s") { parts.push(elSelect(content)); continue; }
    if (typ === "l") { parts.push(elList(content)); continue; }
    if (stripped === "-") { parts.push(elDivider()); continue; }
    if (stripped === "=") { parts.push(elDivider(true)); continue; }
    if (typ === "v") { parts.push(elBadge(content)); continue; }
    if (typ === "a") { parts.push(elAlert(content)); continue; }
    if (typ === "k") { parts.push(elCheckbox(content)); continue; }

    if (typ === "g" || typ === "c" || typ === "r") {
      const children: string[] = [];
      while (i < lines.length) {
        const nxt = lines[i];
        if (!nxt.trim()) { i++; continue; }
        if (indentLevel(nxt) <= lv) break;
        children.push(nxt);
        i++;
      }
      if (typ === "g") {
        parts.push(renderTable(content, children));
      } else if (typ === "c") {
        const [inner] = renderLines(children);
        parts.push(`<div class="card my-[var(--card-margin)] p-[var(--card-padding)] border-2 border-[var(--border-card)] rounded-[var(--card-radius)] bg-[var(--bg-card)] sketchy-card">${inner}</div>`);
      } else {
        const [inner] = renderLines(children);
        parts.push(`<div class="flex gap-4 items-start flex-wrap">${inner}</div>`);
      }
      continue;
    }

    parts.push(elText(raw.trimStart()));
  }
  return [parts.join("\n"), i];
}

export function renderCup(cup: string, _theme?: string): string {
  // Theme override could load from file; for MCP we use default only for now
  const theme = DEFAULT_THEME;
  const lines = cup.split("\n");
  const [inner] = renderLines(lines);
  return pageWrap(theme, inner);
}
