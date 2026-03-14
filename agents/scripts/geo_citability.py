#!/usr/bin/env python3
"""
GEO Citability Scorer - Analyzes web content for AI search citation potential.

Fetches a URL, segments content into blocks, and scores each block on
5 criteria: answer quality, self-containment, readability, stat density, uniqueness.

Usage: python3 geo_citability.py <URL>
Output: JSON with overall score, top/bottom passages, recommendations

Requirements: beautifulsoup4, requests
"""

import json
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def fetch_page(url: str) -> str:
    """Fetch page content with appropriate headers."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GEOAudit/1.0)",
        "Accept": "text/html,application/xhtml+xml",
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def extract_content_blocks(html: str) -> list[dict]:
    """Extract meaningful content blocks from HTML."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    blocks = []

    # Extract from semantic elements first, then fall back to paragraphs
    content_tags = soup.find_all(["article", "section", "main"])
    if not content_tags:
        content_tags = [soup.body] if soup.body else [soup]

    for container in content_tags:
        # Get headings with their following content
        for heading in container.find_all(["h1", "h2", "h3"]):
            heading_text = heading.get_text(strip=True)
            content_parts = []
            for sibling in heading.find_next_siblings():
                if sibling.name in ["h1", "h2", "h3"]:
                    break
                text = sibling.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)

            if content_parts:
                block_text = " ".join(content_parts)
                blocks.append({
                    "heading": heading_text,
                    "text": block_text,
                    "tag": heading.name,
                })

        # Standalone paragraphs not under headings
        for p in container.find_all("p"):
            text = p.get_text(strip=True)
            if len(text) > 80 and not any(text in b["text"] for b in blocks):
                blocks.append({
                    "heading": None,
                    "text": text,
                    "tag": "p",
                })

    return blocks


def score_answer_quality(block: dict) -> float:
    """Score how well the block answers a potential question (0-1)."""
    text = block["text"]
    heading = block.get("heading", "") or ""
    score = 0.0

    # Q&A heading pattern bonus
    qa_patterns = [r"^what\s", r"^how\s", r"^why\s", r"^when\s", r"^who\s", r"^is\s", r"^can\s", r"^does\s"]
    if any(re.match(p, heading.lower()) for p in qa_patterns):
        score += 0.3

    # Direct statement opening (not filler)
    first_sentence = text.split(".")[0] if "." in text else text[:100]
    filler_starts = ["in today's", "it's no secret", "as we all know", "in this article"]
    if not any(first_sentence.lower().startswith(f) for f in filler_starts):
        score += 0.2

    # Definitional patterns
    definitional = [r"\bis\s+(?:a|an|the)\s", r"\brefers\s+to\b", r"\bmeans\s", r"\bdefined\s+as\b"]
    if any(re.search(p, text.lower()) for p in definitional):
        score += 0.2

    # Ideal citation length (134-167 ideal, 50-300 acceptable)
    word_count = len(text.split())
    if 100 <= word_count <= 300:
        score += 0.2
    elif 50 <= word_count <= 500:
        score += 0.1

    # Concluding/summarizing quality
    if re.search(r"\b(therefore|thus|in summary|overall|as a result)\b", text.lower()):
        score += 0.1

    return min(score, 1.0)


def score_self_containment(block: dict) -> float:
    """Score how well the block stands alone without context (0-1)."""
    text = block["text"]
    score = 0.5

    # Penalize dangling references
    dangling = [r"\bthis\s+(?:is|was|means)\b", r"\bthat\s+(?:is|was)\b", r"\bas\s+mentioned\b",
                r"\bsee\s+above\b", r"\bsee\s+below\b", r"\bas\s+shown\b"]
    dangling_count = sum(1 for p in dangling if re.search(p, text.lower()))
    score -= dangling_count * 0.1

    # Reward if heading terms appear in text
    if block.get("heading"):
        heading_words = set(block["heading"].lower().split()) - {"the", "a", "an", "is", "of", "and", "or", "for", "to", "in", "on", "at", "how", "what", "why"}
        text_lower = text.lower()
        matches = sum(1 for w in heading_words if w in text_lower)
        if heading_words and matches / len(heading_words) > 0.5:
            score += 0.2

    # Reward proper nouns / specific entities
    proper_nouns = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    if len(proper_nouns) >= 2:
        score += 0.15

    # Reward complete sentences
    sentence_count = len(re.findall(r"[.!?]\s", text))
    if sentence_count >= 2:
        score += 0.15

    return max(0.0, min(score, 1.0))


def score_readability(block: dict) -> float:
    """Score readability -- clear, accessible language (0-1)."""
    text = block["text"]
    words = text.split()
    word_count = len(words)
    if word_count == 0:
        return 0.0

    score = 0.5

    # Average word length
    avg_word_len = sum(len(w) for w in words) / word_count
    if avg_word_len < 5:
        score += 0.2
    elif avg_word_len < 6:
        score += 0.1
    elif avg_word_len > 7:
        score -= 0.1

    # Sentence length
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if sentences:
        avg_sentence_len = word_count / len(sentences)
        if avg_sentence_len < 15:
            score += 0.15
        elif avg_sentence_len < 20:
            score += 0.1
        elif avg_sentence_len > 30:
            score -= 0.15

    # Jargon/complexity penalty
    complex_words = [w for w in words if len(w) > 12]
    if len(complex_words) / max(word_count, 1) > 0.1:
        score -= 0.15

    # Structured formatting bonus
    if re.search(r"\b\d+\.\s|\b[a-z]\)\s", text):
        score += 0.1

    return max(0.0, min(score, 1.0))


def score_stat_density(block: dict) -> float:
    """Score density of specific facts, numbers, dates, comparisons (0-1)."""
    text = block["text"]
    score = 0.0

    # Numbers (percentages, dollar amounts, quantities)
    numbers = re.findall(r"\b\d+(?:\.\d+)?(?:\s*%|\s*x|\s*times)?\b", text)
    if len(numbers) >= 3:
        score += 0.3
    elif len(numbers) >= 1:
        score += 0.15

    # Dates and years
    dates = re.findall(r"\b(?:19|20)\d{2}\b|\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b", text)
    if dates:
        score += 0.2

    # Comparisons
    comparisons = re.findall(r"\b(?:more than|less than|compared to|versus|vs\.?|higher|lower|faster|slower|better|worse)\b", text.lower())
    if comparisons:
        score += 0.2

    # Specific entities
    proper = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
    if len(proper) >= 3:
        score += 0.15

    # Currency
    money = re.findall(r"\$[\d,]+(?:\.\d{2})?|\b\d+\s*(?:dollars|euros|USD|EUR)\b", text)
    if money:
        score += 0.15

    return min(score, 1.0)


def score_uniqueness(block: dict) -> float:
    """Score originality vs generic/filler content (0-1)."""
    text = block["text"].lower()
    score = 0.6

    # Penalize generic filler
    filler = [
        "in today's world", "it's no secret that", "at the end of the day",
        "in today's fast-paced", "look no further", "one-stop shop",
        "game changer", "best-in-class", "cutting-edge", "state-of-the-art",
        "leverage", "synergy", "paradigm shift", "think outside the box",
        "take it to the next level", "revolutionize", "disrupt",
    ]
    filler_count = sum(1 for f in filler if f in text)
    score -= filler_count * 0.15

    # Reward original content signals
    if re.search(r"\b(?:we|our|I)\s+(?:found|discovered|built|tested|measured|observed)\b", text):
        score += 0.2

    # Reward quotes or attributions
    if re.search(r'["\u201c].*?["\u201d]|according to\b', text):
        score += 0.15

    # Penalize very short blocks
    if len(text.split()) < 30:
        score -= 0.2

    return max(0.0, min(score, 1.0))


def analyze_url(url: str) -> dict:
    """Run full citability analysis on a URL."""
    html = fetch_page(url)
    blocks = extract_content_blocks(html)

    if not blocks:
        return {
            "url": url,
            "error": "No content blocks extracted",
            "overall_score": 0,
            "recommendations": ["Page appears to have no extractable content. Check if content is JS-rendered."],
        }

    scored_blocks = []
    for block in blocks:
        scores = {
            "answer_quality": score_answer_quality(block),
            "self_containment": score_self_containment(block),
            "readability": score_readability(block),
            "stat_density": score_stat_density(block),
            "uniqueness": score_uniqueness(block),
        }

        weights = {"answer_quality": 0.30, "self_containment": 0.25, "readability": 0.20, "stat_density": 0.15, "uniqueness": 0.10}
        composite = sum(scores[k] * weights[k] for k in weights)

        scored_blocks.append({
            "heading": block.get("heading"),
            "text_preview": block["text"][:150] + "..." if len(block["text"]) > 150 else block["text"],
            "word_count": len(block["text"].split()),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "composite": round(composite, 2),
        })

    scored_blocks.sort(key=lambda x: x["composite"], reverse=True)

    overall = sum(b["composite"] for b in scored_blocks) / len(scored_blocks) if scored_blocks else 0

    # Generate recommendations
    recommendations = []
    avg_scores = {}
    for key in ["answer_quality", "self_containment", "readability", "stat_density", "uniqueness"]:
        avg = sum(b["scores"][key] for b in scored_blocks) / len(scored_blocks) if scored_blocks else 0
        avg_scores[key] = round(avg, 2)

    if avg_scores.get("answer_quality", 0) < 0.4:
        recommendations.append("Use Q&A heading patterns (## What is X?) and lead with direct answers")
    if avg_scores.get("self_containment", 0) < 0.4:
        recommendations.append("Reduce dangling references (this, that, above). Name subjects explicitly")
    if avg_scores.get("readability", 0) < 0.4:
        recommendations.append("Simplify language: shorter sentences, fewer complex words")
    if avg_scores.get("stat_density", 0) < 0.3:
        recommendations.append("Add specific numbers, dates, comparisons, and data points")
    if avg_scores.get("uniqueness", 0) < 0.4:
        recommendations.append("Replace generic filler phrases with specific, original insights")
    if not recommendations:
        recommendations.append("Content is well-optimized for AI citations")

    return {
        "url": url,
        "blocks_analyzed": len(scored_blocks),
        "overall_score": round(overall * 100, 1),
        "average_scores": avg_scores,
        "top_passages": scored_blocks[:3],
        "bottom_passages": scored_blocks[-3:] if len(scored_blocks) > 3 else [],
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 geo_citability.py <URL>"}))
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    try:
        result = analyze_url(url)
        print(json.dumps(result, indent=2))
    except requests.exceptions.RequestException as e:
        print(json.dumps({"error": f"Failed to fetch URL: {e}", "url": url}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Analysis failed: {e}", "url": url}))
        sys.exit(1)
