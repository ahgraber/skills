# Visual Companion Guide

Browser-based visual brainstorming companion for showing mockups, diagrams, and options.

Routing rules (browser vs terminal) are in `SKILL.md` — consult those before picking a medium.

## How It Works

The server watches a directory for HTML files and serves the newest one to the browser.
You write HTML content to `screen_dir`, the user sees it in their browser and can click to select options.
Selections are recorded to `state_dir/events` that you read on your next turn.

**Content fragments vs full documents:** If your HTML file starts with `<!DOCTYPE` or `<html`, the server serves it as-is (just injects the helper script).
Otherwise, the server automatically wraps your content in the frame template — adding the header, CSS theme, selection indicator, and all interactive infrastructure.
**Write content fragments by default.**
Only write full documents when you need complete control over the page.

## Starting a Session

The SKILL.md startup question determines which command to run:

```bash
# Ephemeral (default — user said no or didn't care)
skills/visual-brainstorming/scripts/start-server.sh

# Persistent (user wants wireframes saved)
skills/visual-brainstorming/scripts/start-server.sh --project-dir /path/they/specified

# Returns: {"type":"server-started","port":52341,"url":"http://localhost:52341",
#           "screen_dir":"<session>/content",
#           "state_dir":"<session>/state"}
```

Save `screen_dir` and `state_dir` from the response.
Tell user to open the URL.

**Finding connection info:** The server writes its startup JSON to `$STATE_DIR/server-info`.
If you launched the server in the background and didn't capture stdout, read that file to get the URL and port.

### Choosing the right launch mode

The script has two modes.
Which one to use depends on two properties of your environment:

- **Does the harness reap detached background processes** when a tool call completes?
  (Windows/Git Bash and Codex are auto-detected and handled; anything else that reaps requires `--foreground`.)
- **Does your tool call block** until the command exits, or does it return immediately?

| Script mode                             | When to use                                                                                   | What the tool call does                                                                                                                                                  |
| --------------------------------------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Default (self-backgrounds with `nohup`) | Environment does not reap background processes                                                | Blocking — the script exits after printing JSON; use a normal synchronous call                                                                                           |
| `--foreground`                          | Environment reaps background processes, OR the tool call is already non-blocking/backgrounded | Non-blocking — script runs indefinitely; use your harness's async or background call mechanism, then read `$STATE_DIR/server-info` on the next turn for the URL and port |

Using `--foreground` with a blocking tool call will hang the turn.
Using default mode with a background tool call works but double-backgrounds the server, which makes lifecycle harder to debug.

Windows/Git Bash and Codex (`CODEX_CI` env var) are auto-detected: the script switches to foreground mode automatically, so you only need to ensure the tool call is non-blocking.

**Owner-process monitoring** is disabled by default.
The 30-minute idle timeout and explicit `stop-server.sh` are sufficient for cleanup.
Pass `--owner-monitor` only if you are certain the grandparent PID of this script is a stable, long-lived process across all turns (not a per-call sandbox orchestrator).

If the URL is unreachable from your browser (common in remote/containerized setups), bind a non-loopback host:

```bash
skills/visual-brainstorming/scripts/start-server.sh \
  --project-dir /path/to/project \
  --host 0.0.0.0 \
  --url-host localhost
```

Use `--url-host` to control what hostname is printed in the returned URL JSON.

## The Loop

1. **Check server is alive**, then **write HTML** to a new file in `screen_dir`:

   - Before each write, check that `$STATE_DIR/server-info` exists.
     If it doesn't (or `$STATE_DIR/server-stopped` exists), the server has shut down — restart it with `start-server.sh` before continuing.
     The server auto-exits after 30 minutes of inactivity.
   - Use semantic filenames: `platform.html`, `visual-style.html`, `layout.html`
   - **Never reuse filenames** — each screen gets a fresh file
   - Use Write tool — **never use cat/heredoc** (dumps noise into terminal)
   - Server automatically serves the newest file

2. **Tell user what to expect and end your turn:**

   - Remind them of the URL (every step, not just first)
   - Give a brief text summary of what's on screen (e.g., "Showing 3 layout options for the homepage")
   - Make the turn-model explicit: a browser click alone will NOT advance the conversation — the harness only acts on terminal input.
     Always ask the user to type a reply (even one character) so you get a turn to read their selection.
     For example: "Click your pick, then type anything in the terminal — even the option letter — so I can continue."

3. **On your next turn** — after the user responds in the terminal:

   - Read `$STATE_DIR/events` if it exists — this contains the user's browser interactions (clicks, selections) as JSON lines
   - Merge with the user's terminal text to get the full picture
   - The terminal message is the primary feedback; `state_dir/events` provides structured interaction data

4. **Iterate or advance** — if feedback changes current screen, write a new file (e.g., `layout-v2.html`).
   Only move to the next question when the current step is validated.

5. **Unload when returning to terminal** — when the next step doesn't need the browser (e.g., a clarifying question, a tradeoff discussion), push a waiting screen to clear the stale content:

   ```html
   <!-- filename: waiting.html (or waiting-2.html, etc.) -->
   <div style="display:flex;align-items:center;justify-content:center;min-height:60vh">
     <p class="subtitle">Continuing in terminal...</p>
   </div>
   ```

   This prevents the user from staring at a resolved choice while the conversation has moved on.
   When the next visual question comes up, push a new content file as usual.

6. Repeat until done.

## Writing Content Fragments

Write just the content that goes inside the page.
The server wraps it in the frame template automatically (header, theme CSS, selection indicator, and all interactive infrastructure).

**Minimal example:**

```html
<h2>Which layout works better?</h2>
<p class="subtitle">Consider readability and visual hierarchy</p>

<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>Single Column</h3>
      <p>Clean, focused reading experience</p>
    </div>
  </div>
  <div class="option" data-choice="b" onclick="toggleSelect(this)">
    <div class="letter">B</div>
    <div class="content">
      <h3>Two Column</h3>
      <p>Sidebar navigation with main content</p>
    </div>
  </div>
</div>
```

That's it.
No `<html>`, no CSS, no `<script>` tags needed.
The server provides all of that.

## CSS Classes Available

The frame template provides these CSS classes for your content:

### Options (A/B/C choices)

```html
<div class="options">
  <div class="option" data-choice="a" onclick="toggleSelect(this)">
    <div class="letter">A</div>
    <div class="content">
      <h3>Title</h3>
      <p>Description</p>
    </div>
  </div>
</div>
```

**Multi-select:** Add `data-multiselect` to the container to let users select multiple options.
Each click toggles the item.
The indicator bar shows the count.

```html
<div class="options" data-multiselect>
  <!-- same option markup — users can select/deselect multiple -->
</div>
```

### Cards (visual designs)

```html
<div class="cards">
  <div class="card" data-choice="design1" onclick="toggleSelect(this)">
    <div class="card-image"><!-- mockup content --></div>
    <div class="card-body">
      <h3>Name</h3>
      <p>Description</p>
    </div>
  </div>
</div>
```

### Mockup container

```html
<div class="mockup">
  <div class="mockup-header">Preview: Dashboard Layout</div>
  <div class="mockup-body"><!-- your mockup HTML --></div>
</div>
```

### Split view (side-by-side)

```html
<div class="split">
  <div class="mockup"><!-- left --></div>
  <div class="mockup"><!-- right --></div>
</div>
```

### Pros/Cons

```html
<div class="pros-cons">
  <div class="pros"><h4>Pros</h4><ul><li>Benefit</li></ul></div>
  <div class="cons"><h4>Cons</h4><ul><li>Drawback</li></ul></div>
</div>
```

### Mock elements (wireframe building blocks)

```html
<div class="mock-nav">Logo | Home | About | Contact</div>
<div style="display: flex;">
  <div class="mock-sidebar">Navigation</div>
  <div class="mock-content">Main content area</div>
</div>
<button class="mock-button">Action Button</button>
<input class="mock-input" placeholder="Input field">
<div class="placeholder">Placeholder area</div>
```

### Typography and sections

- `h2` — page title
- `h3` — section heading
- `.subtitle` — secondary text below title
- `.section` — content block with bottom margin
- `.label` — small uppercase label text

## Browser Events Format

When the user clicks options in the browser, their interactions are recorded to `$STATE_DIR/events` (one JSON object per line).
The file is cleared automatically when you push a new screen.

```jsonl
{"type":"click","choice":"a","text":"Option A - Simple Layout","timestamp":1706000101}
{"type":"click","choice":"c","text":"Option C - Complex Grid","timestamp":1706000108}
{"type":"click","choice":"b","text":"Option B - Hybrid","timestamp":1706000115}
```

The full event stream shows the user's exploration path — they may click multiple options before settling.
The last `choice` event is typically the final selection, but the pattern of clicks can reveal hesitation or preferences worth asking about.

If `$STATE_DIR/events` doesn't exist, the user didn't interact with the browser — use only their terminal text.

## Design Tips

- **Scale fidelity to the question** — wireframes for layout, polish for polish questions
- **Explain the question on each page** — "Which layout feels more professional?"
  not just "Pick one"
- **Iterate before advancing** — if feedback changes current screen, write a new version
- **2-4 options max** per screen
- **Use real content when it matters** — for a photography portfolio, use actual images (Unsplash).
  Placeholder content obscures design issues.
- **Keep mockups simple** — focus on layout and structure, not pixel-perfect design

## File Naming

- Use semantic names: `platform.html`, `visual-style.html`, `layout.html`
- Never reuse filenames — each screen must be a new file
- For iterations: append version suffix like `layout-v2.html`, `layout-v3.html`
- Server serves newest file by modification time

## Cleaning Up

```bash
skills/visual-brainstorming/scripts/stop-server.sh $SESSION_DIR
```

Ephemeral sessions (`$TMPDIR`) are deleted on stop.
Persistent sessions (`--project-dir`) keep the content directory so the user can review saved mockups; only the server state files are removed.

## Reference

- Frame template (CSS reference): `skills/visual-brainstorming/scripts/frame-template.html`
- Helper script (client-side): `skills/visual-brainstorming/scripts/helper.js`
