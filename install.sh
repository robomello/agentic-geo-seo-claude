#!/usr/bin/env bash
# Install agentic-geo-seo-claude into your Claude Code setup
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${HOME}/.claude"

echo "Installing agentic-geo-seo-claude..."
echo ""

# Check prerequisites
command -v jq >/dev/null 2>&1 || { echo "ERROR: jq is required. Install with: sudo apt install jq"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 is required."; exit 1; }
python3 -c "import requests" 2>/dev/null || { echo "WARNING: 'requests' not installed. Run: pip install requests"; }
python3 -c "import bs4" 2>/dev/null || { echo "WARNING: 'beautifulsoup4' not installed. Run: pip install beautifulsoup4"; }

# Create directories
mkdir -p "${CLAUDE_DIR}/hooks"
mkdir -p "${CLAUDE_DIR}/agents/scripts"

# Copy hook
cp "${SCRIPT_DIR}/hooks/geo-check.sh" "${CLAUDE_DIR}/hooks/geo-check.sh"
chmod +x "${CLAUDE_DIR}/hooks/geo-check.sh"
echo "  Installed hook: ~/.claude/hooks/geo-check.sh"

# Copy agent
cp "${SCRIPT_DIR}/agents/geo-audit-agent.md" "${CLAUDE_DIR}/agents/geo-audit-agent.md"
echo "  Installed agent: ~/.claude/agents/geo-audit-agent.md"

# Copy scripts
cp "${SCRIPT_DIR}/agents/scripts/geo_citability.py" "${CLAUDE_DIR}/agents/scripts/geo_citability.py"
cp "${SCRIPT_DIR}/agents/scripts/geo_crawler_check.py" "${CLAUDE_DIR}/agents/scripts/geo_crawler_check.py"
echo "  Installed scripts: ~/.claude/agents/scripts/geo_*.py"

# Register hook in settings.json
SETTINGS="${CLAUDE_DIR}/settings.json"
if [ -f "$SETTINGS" ]; then
    # Check if hook is already registered
    if grep -q "geo-check.sh" "$SETTINGS"; then
        echo "  Hook already registered in settings.json"
    else
        echo ""
        echo "  NOTE: Add this to your settings.json PostToolUse array:"
        echo ""
        echo '  {'
        echo '    "matcher": "Write",'
        echo '    "hooks": ['
        echo '      {'
        echo '        "type": "command",'
        echo '        "command": "'"${CLAUDE_DIR}"'/hooks/geo-check.sh",'
        echo '        "timeout": 5000'
        echo '      }'
        echo '    ]'
        echo '  }'
        echo ""
    fi
else
    echo "  NOTE: No settings.json found. Create one and register the hook manually."
fi

echo ""
echo "Installation complete."
echo ""
echo "Optional: Append GEO sections to your skills:"
echo "  - skills/frontend-design-geo.md -> append to your frontend-design SKILL.md"
echo "  - skills/copywriting-geo.md -> append to your copywriting SKILL.md"
echo "  - skills/deploy-agent-geo.md -> append to your deploy-agent.md"
echo ""
echo "Test the scripts:"
echo "  python3 ~/.claude/agents/scripts/geo_crawler_check.py example.com"
echo "  python3 ~/.claude/agents/scripts/geo_citability.py example.com"
