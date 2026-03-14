# Agentic GEO SEO for Claude Code

Built by [Roberto de Mello](https://github.com/rdemello) / [SynAI](https://synai.ai)

Auto-triggering GEO (Generative Engine Optimization) for [Claude Code](https://claude.ai/claude-code). No slash commands. No manual audits. Just write HTML and get GEO feedback automatically.

We saw [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) (2.3k stars) and liked the idea, but didn't like that it required remembering to run `/geo audit`. We rebuilt it as a fully agentic system that fits into Claude Code's hook/agent/skill architecture. Zero new commands.

## The Problem

AI search engines (ChatGPT, Perplexity, Claude, Google AI Overviews) are replacing traditional search for a growing chunk of queries. Traditional SEO optimizes for link-based ranking. GEO optimizes for **citability** -- whether an AI engine will quote your content in its response.

Most devs don't think about GEO while building. By the time someone runs an audit, the page is already live with missing meta descriptions, no JSON-LD, thin content, and a robots.txt that blocks half the AI crawlers.

## Our Approach: Three Layers, Zero Commands

### Layer 1: PostToolUse Hook

Every time Claude Code writes an `.html` file, a lightweight bash hook (<500ms, pure grep) checks for:

- Missing `<meta name="description">`
- Missing JSON-LD structured data
- No `<h1>` heading
- Thin content (<200 words)

Advisory only. Never blocks. Content-hash debounced so you see warnings once per file, not on every save.

### Layer 2: Skill Injections

GEO sections appended to skills that already auto-trigger:

- **frontend-design** -- meta descriptions, JSON-LD, semantic HTML, SSR, AI crawler access meta tags
- **copywriting** -- citable passage structure (134-167 words), Q&A headings, fact density, E-E-A-T
- **deploy-agent** -- post-deploy GEO spot-check on public web services

You ask Claude to "build a landing page" and GEO practices are baked into the output. No extra prompting.

### Layer 3: Deep Audit Agent

On-demand thorough analysis via two purpose-built Python scripts:

```
Agent(subagent_type="geo-audit-agent", prompt="Audit drinkwaretrove.com")
```

Returns crawler access matrix, citability scores per content block, technical GEO findings, and prioritized fix list. Runs on Haiku to keep costs minimal.

## What's In the Box

```
agentic-geo-seo-claude/
  hooks/
    geo-check.sh              # PostToolUse hook (bash, <500ms)
  agents/
    geo-audit-agent.md        # Claude Code agent definition
    scripts/
      geo_citability.py       # Content citability scorer
      geo_crawler_check.py    # AI crawler access analyzer
  skills/
    frontend-design-geo.md    # GEO section for frontend skill
    copywriting-geo.md        # GEO section for copywriting skill
    deploy-agent-geo.md       # GEO section for deploy agent
  install.sh                  # One-command installer
```

## Install

```bash
git clone https://github.com/rdemello/agentic-geo-seo-claude.git
cd agentic-geo-seo-claude
chmod +x install.sh && ./install.sh
```

Then register the hook in `~/.claude/settings.json` under `PostToolUse`:

```json
{
  "matcher": "Write",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/geo-check.sh",
      "timeout": 5000
    }
  ]
}
```

Append the skill sections from `skills/*.md` into your existing skills. Or don't -- the hook and agent work standalone.

## Standalone Usage

The Python scripts work without Claude Code:

```bash
# Which AI crawlers can reach your site?
python3 agents/scripts/geo_crawler_check.py drinkwaretrove.com

# How citable is your content?
python3 agents/scripts/geo_citability.py drinkwaretrove.com
```

Both output JSON. Pipe to `jq` for pretty printing, or consume programmatically.

## 14 AI Crawlers Checked

| Crawler | Org | Purpose |
|---------|-----|---------|
| GPTBot | OpenAI | ChatGPT training/search |
| ChatGPT-User | OpenAI | ChatGPT browsing |
| OAI-SearchBot | OpenAI | SearchGPT |
| ClaudeBot | Anthropic | Claude training |
| anthropic-ai | Anthropic | Anthropic AI |
| PerplexityBot | Perplexity | Perplexity search |
| Google-Extended | Google | Gemini training |
| Bytespider | ByteDance | TikTok/Doubao |
| CCBot | Common Crawl | Open dataset |
| Amazonbot | Amazon | Alexa/Amazon AI |
| FacebookBot | Meta | Meta AI |
| Meta-ExternalAgent | Meta | Meta AI training |
| Applebot-Extended | Apple | Apple Intelligence |
| cohere-ai | Cohere | Cohere AI training |

## Citability Scoring

Each content block on your page is scored on 5 weighted criteria:

| Criterion | Weight | What We Measure |
|-----------|--------|-----------------|
| Answer Quality | 30% | Does this passage directly answer a question? Q&A heading patterns, definitional language, direct statements |
| Self-Containment | 25% | Can an AI quote this without needing surrounding context? No dangling "this/that" references |
| Readability | 20% | Clear sentences, accessible vocabulary, reasonable length |
| Stat Density | 15% | Numbers, dates, percentages, comparisons. AI engines love citing concrete data |
| Uniqueness | 10% | Original insight vs "cutting-edge synergy" filler |

## Why We Built This

We run 8+ businesses with public-facing websites. Every site needs to perform in AI search, not just traditional Google. Manually auditing each page wasn't scaling. Now GEO awareness is ambient -- it's part of the build process, not an afterthought.

The agentic pattern (hooks + skill injection + on-demand agent) is how we think about all cross-cutting concerns: if it matters, it should trigger automatically.

## Requirements

- Claude Code CLI
- Python 3.10+ with `beautifulsoup4` and `requests`
- `jq` (for the bash hook)

## License

MIT -- use it, fork it, improve it.
