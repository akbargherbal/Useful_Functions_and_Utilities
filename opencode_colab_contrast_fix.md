# opencode low-contrast / gray background in Google Colab terminal

## Symptom

When `opencode` is launched inside the Google Colab terminal, the TUI renders
with light text on a **medium-gray** canvas, producing low contrast. The normal
shell prompt (before launching opencode) is white on near-black and looks fine.

- `01_colab_screenshot.png` — Colab terminal before opencode: dark background, high contrast.
- `02_colab_screenshot.png` — opencode running: gray canvas, light text, low contrast.

## Root cause

This is a **frontend / DOM styling issue**, specifically the ANSI color palette
configured by Colab for its xterm.js terminal. It is **not** an opencode rendering
bug and **not** a Colab backend/environment issue.

Colab overrides ANSI color 0 ("black") to gray `#7f7f7f`. opencode draws its
canvas background using ANSI black (`\x1b[40m` / `48;5;0`). Because the palette
maps index 0 to gray instead of black, the canvas becomes gray while the text
stays light.

### Evidence

Read directly from the live page over Chrome DevTools Protocol (`localhost:9222`):

```
document.querySelector('colab-xterm-terminal').terminal.options.theme
```

Returned:

```json
{
  "background": "#282a2c",
  "foreground": "#fff",
  "black": "#7f7f7f",
  "brightBlack": "#7f7f7f",
  "white": "",
  "brightWhite": "",
  "blue": "#82b1ff",
  "brightBlue": "#5c5cff",
  "...": "..."
}
```

The offending cell in the terminal's DOM:

```html
<span class="xterm-bg-0 xterm-fg-7" ...>
```

```js
getComputedStyle(span).backgroundColor   // "rgb(127, 127, 127)"  -> gray, not black
```

- `xterm-bg-0` = ANSI background color 0 ("black") -> Colab maps it to `#7f7f7f`.
- `xterm-fg-7` = ANSI foreground color 7 -> light text.

Result: light text on gray = low contrast. On a standard terminal ANSI 0 is
`#000000`, so the same opencode theme looks correct.

## Fix

### Immediate (current terminal only)

Open Chrome DevTools console while the Colab Terminal tab is open and paste:

```js
const term = document.querySelector('colab-xterm-terminal').terminal;
term.options.theme = { ...term.options.theme, black: '#000000', brightBlack: '#3a3a3a' };
```

This patches the live xterm instance. Verified: `xterm-bg-0` changes from
`rgb(127, 127, 127)` to `rgb(0, 0, 0)` and contrast is restored.

Caveat: the change is lost when the terminal is recreated (new Terminal tab,
reconnect, or page reload).

### Persistent (re-applies for every terminal)

Run this instead, or put it in a Tampermonkey / userscript:

```js
setInterval(() => {
  const t = document.querySelector('colab-xterm-terminal')?.terminal;
  if (t && t.options.theme.black !== '#000000') {
    t.options.theme = { ...t.options.theme, black: '#000000', brightBlack: '#3a3a3a' };
  }
}, 1000);
```

Note: the `colab-xterm-terminal` element must exist (open a Terminal tab first);
the interval retries until it does.

## Alternative (opencode-side, no browser patch)

Before launching opencode in the Colab terminal:

```bash
export COLORTERM=truecolor
opencode
```

This makes opencode emit 24-bit colors (inline `rgb()`), bypassing Colab's
broken ANSI-0 palette. It should survive reloads since it is set in the shell,
but it has **not** been verified in this Colab environment — the console snippet
above is the confirmed fix.
