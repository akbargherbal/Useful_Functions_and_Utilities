# Using Graphify with DeepSeek on a Repo

Graphify turns a codebase into a queryable knowledge graph. Code itself is parsed **locally** via tree-sitter (no LLM needed), but non-code artifacts — docs, PDFs, images, video — need a model backend for semantic extraction. This guide sets that backend to **DeepSeek**.

## 1. Install the CLI

```bash
# Recommended (isolated env)
uv tool install graphifyy

# Alternative
pipx install graphifyy
```

> The PyPI package is `graphifyy` (double-y); the CLI command is still `graphify`.

If `graphify` isn't found right after install, run `uv tool update-shell` (or `pipx ensurepath`) and open a new terminal.

## 2. Get a DeepSeek API key

Set it as an environment variable:

```bash
export DEEPSEEK_API_KEY="sk-..."
```

Add this to your shell profile (`~/.bashrc` / `~/.zshrc`) if you want it to persist across sessions.

## 3. Register the skill with your AI assistant (optional)

If you're using this inside Claude Code, Cursor, Codex, Gemini CLI, etc., register the skill once:

```bash
graphify install
```

This lets you run `/graphify .` inside your assistant. Note: when running through an IDE assistant session, the assistant's own model handles semantic extraction — the `DEEPSEEK_API_KEY` / `--backend deepseek` path below is specifically for **headless** extraction (CLI/CI, no IDE).

## 4. Build the graph on your repo, using DeepSeek

This is a **two-step process**, not one command:

```bash
cd /path/to/your-repo
graphify extract . --backend deepseek --code-only
graphify cluster-only . --backend deepseek
```

- **Step 1 (`extract`)**: parses code locally via tree-sitter (free, no API calls) and writes `graphify-out/graph.json`. With `--code-only`, docs/PDFs/images are skipped entirely — no LLM involved at all in this step.
- **Step 2 (`cluster-only`)**: loads the graph that was just written, re-clusters it into communities, and **labels those communities with an LLM call** (a small, cheap naming pass — not re-extraction). This is what actually produces `GRAPH_REPORT.md` and `graph.html`. Skipping this step leaves you with only `graph.json` and no human-readable report.

If you drop `--code-only` on step 1, docs/PDFs/images also get sent to DeepSeek for semantic extraction at that stage:

```bash
graphify extract . --backend deepseek        # includes docs/PDFs/images via DeepSeek
graphify cluster-only . --backend deepseek
```

Useful variants:

```bash
graphify extract ./docs --backend deepseek --mode deep       # richer semantic extraction
graphify extract ./docs --backend deepseek --token-budget 30000   # smaller chunks
graphify extract . --backend deepseek --force                # overwrite even if graph shrinks
```

## 5. Inspect the output

A successful run produces:

```
graphify-out/
├── graph.html       # open in a browser — click nodes, filter, search
├── GRAPH_REPORT.md  # god nodes, communities, suggested questions
└── graph.json       # the full graph, queryable without re-reading files
```

## 6. Query the graph

```bash
graphify query "what connects auth to the database?"
graphify path "UserService" "DatabasePool"
graphify explain "RateLimiter"
```

Every edge is tagged `EXTRACTED` (explicit in source) or `INFERRED` (resolved by graphify), so you know what's direct vs. derived.

## 7. Keep it fresh

```bash
graphify hook install       # auto re-extract on git commit (AST-only, no API cost)
graphify extract . --backend deepseek --update   # manual re-extraction of changed files only
```

## Notes on DeepSeek specifically

- Only `DEEPSEEK_API_KEY` is required — no base URL override needed unless you're proxying.
- DeepSeek is one of several supported backends (`claude`, `openai`, `gemini`, `deepseek`, `ollama`, `bedrock`, `azure`, `kimi`, `claude-cli`). If multiple keys are set, Graphify auto-detects with this priority: Gemini → Kimi → Claude → OpenAI → DeepSeek → Azure → Bedrock → Ollama — so pass `--backend deepseek` explicitly if you have other keys set and want DeepSeek used.
- Code parsing never touches DeepSeek regardless of backend — only docs/PDFs/images/video go through the API.

## 8. Batch setup across multiple projects

If you keep your repos under one parent folder (e.g. `~/code/`), you can build graphs for all of them in one shot. Remember it's **two commands per repo** — `extract` then `cluster-only`:

```bash
export DEEPSEEK_API_KEY="sk-..."

for dir in ~/code/*/; do
  if [ -d "$dir/.git" ]; then
    echo "== $dir =="
    (cd "$dir" && graphify extract . --backend deepseek --code-only && graphify cluster-only . --backend deepseek)
  fi
done
```

Drop `--code-only` if a given repo has docs/PDFs worth indexing too (that's the part that actually spends DeepSeek tokens; pure code extraction is free either way).

**Manual, quick, one-repo-at-a-time version** (e.g. going through repos one by one in the terminal, arrow-up to repeat):

```bash
cd path/to/project/1
graphify extract . --backend deepseek --code-only
graphify cluster-only . --backend deepseek

cd path/to/project/2
graphify extract . --backend deepseek --code-only    # ↑ arrow, enter
graphify cluster-only . --backend deepseek            # ↑ arrow, enter
```

Both commands are identical across every repo (no project name baked in), so shell history recall works cleanly for the whole batch.

If you want to split the work into two passes across many repos — extract everywhere first, then label/report everywhere — that also works, since `cluster-only` just loads whatever `graph.json` is already on disk:

```bash
# Pass 1: extract only, across all repos
for dir in ~/code/*/; do
  [ -d "$dir/.git" ] && (cd "$dir" && graphify extract . --backend deepseek --code-only)
done

# Pass 2: cluster + report, across all repos that now have a graph.json
for dir in ~/code/*/; do
  [ -f "$dir/graphify-out/graph.json" ] && (cd "$dir" && graphify cluster-only . --backend deepseek)
done
```

To also wire up the "AI agent nudges toward the graph" behavior in each repo (so Claude Code / Codex reach for `graphify query` instead of grepping), add the install step to the same loop:

```bash
for dir in ~/code/*/; do
  if [ -d "$dir/.git" ]; then
    (cd "$dir" && graphify extract . --backend deepseek --code-only && graphify cluster-only . --backend deepseek && graphify claude install && graphify hook install)
  fi
done
```

- `graphify claude install` writes the CLAUDE.md guidance + hook that redirects Claude Code toward the graph (swap for `graphify codex install`, `graphify cursor install`, etc. depending on which assistants you use — you can chain several in the same line).
- `graphify hook install` sets up a **post-commit git hook** so each repo's graph re-extracts automatically after every commit, using AST only (free) — no need to remember to re-run anything for code changes. Docs/PDF changes still need an explicit `--update` pass if you want those re-indexed with DeepSeek.

## 9. One-time bootstrap for a brand-new project

Once you've done the batch setup above, adding a *new* project going forward is just:

```bash
cd ~/code/new-project
graphify extract . --backend deepseek --code-only
graphify cluster-only . --backend deepseek
graphify claude install      # or codex install / cursor install / etc.
graphify hook install
```

Five lines, and that project is graph-ready (graph.json + GRAPH_REPORT.md + graph.html) and self-updating from then on.

## Troubleshooting

- **Empty nodes/edges for docs or PDFs**: confirm `DEEPSEEK_API_KEY` is set and `--backend deepseek` is passed explicitly.
- **`LLM returned invalid JSON` warnings**: the model's output was cut off mid-response. Graphify auto-recovers by re-chunking, but you can raise the cap: `GRAPHIFY_MAX_OUTPUT_TOKENS=16384 graphify extract . --backend deepseek --mode deep`.
- **Rate limiting (429)**: Graphify retries automatically (`GRAPHIFY_MAX_RETRIES`, default 6, honors `Retry-After`). Raise this if you hit DeepSeek's org-level limits often.
