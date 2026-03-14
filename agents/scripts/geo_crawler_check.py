#!/usr/bin/env python3
"""
GEO Crawler Access Checker - Analyzes robots.txt and meta tags for AI crawler access.

Checks 14 AI crawlers, llms.txt, ai.txt, and meta directives.

Usage: python3 geo_crawler_check.py <URL>
Output: JSON with crawler access matrix, score, recommendations

Requirements: requests
"""

import json
import re
import sys
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

# AI crawlers to check
AI_CRAWLERS = [
    {"name": "GPTBot", "org": "OpenAI", "purpose": "ChatGPT training/search"},
    {"name": "ChatGPT-User", "org": "OpenAI", "purpose": "ChatGPT browsing"},
    {"name": "OAI-SearchBot", "org": "OpenAI", "purpose": "SearchGPT"},
    {"name": "ClaudeBot", "org": "Anthropic", "purpose": "Claude training"},
    {"name": "anthropic-ai", "org": "Anthropic", "purpose": "Anthropic AI"},
    {"name": "PerplexityBot", "org": "Perplexity", "purpose": "Perplexity search"},
    {"name": "Google-Extended", "org": "Google", "purpose": "Gemini training"},
    {"name": "Bytespider", "org": "ByteDance", "purpose": "TikTok/Doubao"},
    {"name": "CCBot", "org": "Common Crawl", "purpose": "Open dataset"},
    {"name": "Amazonbot", "org": "Amazon", "purpose": "Alexa/Amazon AI"},
    {"name": "FacebookBot", "org": "Meta", "purpose": "Meta AI"},
    {"name": "Meta-ExternalAgent", "org": "Meta", "purpose": "Meta AI training"},
    {"name": "Applebot-Extended", "org": "Apple", "purpose": "Apple Intelligence"},
    {"name": "cohere-ai", "org": "Cohere", "purpose": "Cohere AI training"},
]


def fetch_robots_txt(base_url: str) -> str | None:
    """Fetch robots.txt content."""
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        resp = requests.get(robots_url, timeout=10)
        if resp.status_code == 200:
            return resp.text
        return None
    except requests.RequestException:
        return None


def check_crawler_access(base_url: str, robots_content: str | None) -> list[dict]:
    """Check each AI crawler's access via robots.txt."""
    results = []

    if robots_content is None:
        for crawler in AI_CRAWLERS:
            results.append({
                **crawler,
                "allowed": True,
                "reason": "No robots.txt found (all allowed)",
            })
        return results

    for crawler in AI_CRAWLERS:
        rp = RobotFileParser()
        rp.parse(robots_content.splitlines())
        allowed = rp.can_fetch(crawler["name"], base_url)

        results.append({
            **crawler,
            "allowed": allowed,
            "reason": "Allowed" if allowed else "Blocked by robots.txt",
        })

    return results


def check_special_files(base_url: str) -> dict:
    """Check for llms.txt and ai.txt files."""
    results = {}

    for filename in ["llms.txt", "ai.txt", "llms-full.txt"]:
        file_url = urljoin(base_url, f"/{filename}")
        try:
            resp = requests.get(file_url, timeout=10)
            if resp.status_code == 200 and len(resp.text.strip()) > 10:
                results[filename] = {
                    "found": True,
                    "size": len(resp.text),
                    "preview": resp.text[:200].strip(),
                }
            else:
                results[filename] = {"found": False}
        except requests.RequestException:
            results[filename] = {"found": False}

    return results


def check_meta_tags(html: str) -> dict:
    """Check for AI-related meta directives in page HTML."""
    results = {
        "noai": False,
        "noimageai": False,
        "max_snippet": None,
        "robots": None,
    }

    robots_meta = re.findall(r'<meta[^>]*name=["\']robots["\'][^>]*content=["\']([^"\']*)["\']', html, re.IGNORECASE)
    if not robots_meta:
        robots_meta = re.findall(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']robots["\']', html, re.IGNORECASE)

    for content in robots_meta:
        results["robots"] = content
        if "noai" in content.lower():
            results["noai"] = True
        if "noimageai" in content.lower():
            results["noimageai"] = True
        snippet_match = re.search(r"max-snippet:\s*(-?\d+)", content)
        if snippet_match:
            results["max_snippet"] = int(snippet_match.group(1))

    return results


def analyze_url(url: str) -> dict:
    """Run full crawler access analysis."""
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    robots_content = fetch_robots_txt(base_url)
    crawlers = check_crawler_access(base_url + "/", robots_content)
    special_files = check_special_files(base_url)

    # Fetch page and check meta tags
    meta_tags = {"noai": False, "noimageai": False, "max_snippet": None, "robots": None}
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (compatible; GEOAudit/1.0)"})
        if resp.status_code == 200:
            meta_tags = check_meta_tags(resp.text)
    except requests.RequestException:
        pass

    # Calculate score
    allowed_count = sum(1 for c in crawlers if c["allowed"])
    total_crawlers = len(crawlers)
    crawler_score = (allowed_count / total_crawlers) * 70

    file_bonus = 0
    if special_files.get("llms.txt", {}).get("found"):
        file_bonus += 15
    if special_files.get("ai.txt", {}).get("found"):
        file_bonus += 10
    if special_files.get("llms-full.txt", {}).get("found"):
        file_bonus += 5

    meta_penalty = 0
    if meta_tags["noai"]:
        meta_penalty += 20
    if meta_tags["noimageai"]:
        meta_penalty += 5
    if meta_tags.get("max_snippet") is not None and 0 <= meta_tags["max_snippet"] < 160:
        meta_penalty += 10

    score = min(100, max(0, crawler_score + file_bonus - meta_penalty))

    # Generate recommendations
    recommendations = []
    blocked = [c for c in crawlers if not c["allowed"]]
    if blocked:
        blocked_names = ", ".join(c["name"] for c in blocked[:5])
        recommendations.append(f"Unblock AI crawlers in robots.txt: {blocked_names}")

    if not special_files.get("llms.txt", {}).get("found"):
        recommendations.append("Add llms.txt with a concise site summary for AI engines")

    if meta_tags["noai"]:
        recommendations.append("Remove 'noai' from robots meta tag to allow AI indexing")

    if meta_tags.get("max_snippet") is not None and 0 <= meta_tags["max_snippet"] < 160:
        recommendations.append("Set max-snippet:-1 to allow full-length AI citations")

    if not blocked and not meta_tags["noai"]:
        recommendations.append("Crawler access is well-configured for AI search visibility")

    return {
        "url": url,
        "robots_txt_found": robots_content is not None,
        "crawlers": [
            {"name": c["name"], "org": c["org"], "allowed": c["allowed"]}
            for c in crawlers
        ],
        "allowed_count": allowed_count,
        "blocked_count": total_crawlers - allowed_count,
        "special_files": special_files,
        "meta_tags": meta_tags,
        "score": round(score, 1),
        "recommendations": recommendations,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: python3 geo_crawler_check.py <URL>"}))
        sys.exit(1)

    url = sys.argv[1]
    if not url.startswith("http"):
        url = "https://" + url

    try:
        result = analyze_url(url)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": f"Analysis failed: {e}", "url": url}))
        sys.exit(1)
