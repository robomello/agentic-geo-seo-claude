#!/usr/bin/env bash
# PostToolUse hook: Advisory GEO checks for HTML files
# Triggers on Write tool for .html files only
# Exit 0 always (advisory only, never blocks)
# Requires: jq, md5sum (coreutils)

set -euo pipefail

INPUT=$(cat)

# Only check Write tool
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null)
[ "$TOOL" = "Write" ] || exit 0

# Extract file path from tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null)
[ -n "$FILE_PATH" ] || exit 0

# Only check .html files
[[ "$FILE_PATH" == *.html ]] || exit 0

# File must exist
[ -f "$FILE_PATH" ] || exit 0

# Debounce: skip if same file content already checked this session
HASH=$(echo "$FILE_PATH" | md5sum | cut -d' ' -f1)
MARKER="/tmp/.geo-check-${HASH}"
if [ -f "$MARKER" ]; then
    CURRENT_HASH=$(md5sum "$FILE_PATH" | cut -d' ' -f1)
    PREV_HASH=$(cat "$MARKER" 2>/dev/null)
    [ "$CURRENT_HASH" = "$PREV_HASH" ] && exit 0
fi

# Save current content hash for debounce
md5sum "$FILE_PATH" | cut -d' ' -f1 > "$MARKER"

# Strip script and style tags for content analysis
CONTENT=$(sed '/<script/,/<\/script>/d; /<style/,/<\/style>/d' "$FILE_PATH")
WARNINGS=()

# Check: missing meta description
if ! grep -qi '<meta[^>]*name=["\x27]description["\x27]' "$FILE_PATH"; then
    WARNINGS+=("Missing <meta name=\"description\"> -- AI search engines use this for snippet generation")
fi

# Check: missing JSON-LD structured data
if ! grep -q 'application/ld+json' "$FILE_PATH"; then
    WARNINGS+=("No JSON-LD structured data -- helps AI engines understand page context")
fi

# Check: missing h1
if ! grep -qi '<h1' "$FILE_PATH"; then
    WARNINGS+=("No <h1> heading -- primary topic signal for AI crawlers")
fi

# Check: thin content (less than 200 words)
WORD_COUNT=$(echo "$CONTENT" | sed 's/<[^>]*>//g' | wc -w)
if [ "$WORD_COUNT" -lt 200 ]; then
    WARNINGS+=("Thin content (~${WORD_COUNT} words) -- AI engines prefer 200+ words for citation")
fi

# Output warnings if any
if [ ${#WARNINGS[@]} -gt 0 ]; then
    echo ""
    echo "GEO Advisory (AI Search Optimization):"
    for w in "${WARNINGS[@]}"; do
        echo "  - $w"
    done
    echo ""
fi

exit 0
