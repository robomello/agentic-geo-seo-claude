# GEO Awareness Section for frontend-design Skill

Append this section to your `~/.claude/skills/frontend-design/SKILL.md` file.

---

## GEO Awareness (AI Search Optimization)

Every HTML page you build must be optimized for AI search engines (ChatGPT, Perplexity, Claude, Google AI Overviews). These are not optional extras -- they are baseline requirements:

- **Meta description**: Always include `<meta name="description" content="...">` (150-160 chars, phrased to answer a question)
- **JSON-LD structured data**: Add `<script type="application/ld+json">` with appropriate schema (Organization, WebPage, Article, Product, FAQ, etc.)
- **First 200 words**: Must be self-contained and fact-rich. AI engines pull citations from the opening content. No filler intros like "Welcome to our site"
- **Semantic HTML**: Use `<article>`, `<section>`, `<nav>`, `<main>`, `<header>`, `<footer>`. AI crawlers rely on structure to understand content hierarchy
- **Server-side rendering**: Content must be visible in raw HTML. GPTBot, ClaudeBot, PerplexityBot cannot execute JavaScript. Critical content must not be JS-rendered only
- **AI crawler access**: Include `<meta name="robots" content="index, follow, max-snippet:-1">` to allow full-length AI citations
- **H1 tag**: Every page needs exactly one `<h1>` that clearly describes the page topic
- **Open Graph tags**: Include `og:title`, `og:description`, `og:image` for social sharing and AI context
