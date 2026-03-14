# GEO Section for deploy-agent

Append this section to your `~/.claude/agents/deploy-agent.md` file, after the Error Handling section.

---

### 6. Post-deploy GEO spot-check (web services only)

If the service has a public URL (synai.ai subdomain or custom domain), run a quick GEO spot-check after the health check passes:

```bash
HTML=$(curl -s --max-time 5 "${PUBLIC_URL}" | head -200)

# Check for GEO basics
echo "$HTML" | grep -qi 'meta.*name.*description' || echo "GEO Warning: No meta description found"
echo "$HTML" | grep -q 'application/ld+json' || echo "GEO Warning: No JSON-LD structured data"
echo "$HTML" | grep -qi '<h1' || echo "GEO Warning: No <h1> tag found"
```

Also check robots.txt if it exists:
```bash
ROBOTS=$(curl -s --max-time 3 "${PUBLIC_URL}/robots.txt")
if [ -n "$ROBOTS" ]; then
    for BOT in GPTBot ClaudeBot PerplexityBot; do
        if echo "$ROBOTS" | grep -A1 "User-agent: $BOT" | grep -q "Disallow: /"; then
            echo "GEO Warning: robots.txt blocks $BOT"
        fi
    done
fi
```

Report any GEO warnings in the deploy output. These are advisory only and do not affect deploy success/failure.
