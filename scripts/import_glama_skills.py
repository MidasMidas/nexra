import hashlib
import json
import re
import subprocess
import sys
import time
import urllib.parse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed


GLAMA_BASE = "https://glama.ai/mcp/servers"
TARGET_COUNT = 3000
OUTPUT_PATH = r"C:\Workspace\nexra\backend_py\data\skills.json"
REPORT_PATH = r"C:\Workspace\nexra\backend_py\data\skills-import-report.json"


CATEGORY_TERMS = [
    "Developer Tools",
    "Local",
    "File Systems",
    "Python",
    "TypeScript",
    "Hybrid",
    "Remote",
    "Shell Access",
    "Code Analysis",
    "App Automation",
    "Command Line",
    "Search",
    "OS Automation",
    "Security",
    "Version Control",
    "Code Execution",
    "Databases",
    "Documentation Access",
    "Autonomous Agents",
    "Multimedia Processing",
    "Prompts",
    "Resources",
    "Image Video Processing",
    "Note Taking",
    "RAG Systems",
    "Cloud Platforms",
    "Knowledge Memory",
    "Agent Orchestration",
    "Text Summarization",
    "Cloud Storage",
    "Penetration Testing",
    "Official",
    "CI CD DevOps",
    "Location Services",
    "E-commerce Retail",
    "Entertainment Media",
    "Content Management Systems",
    "Project Management",
    "Communication",
    "Marketing",
    "Vector Databases",
    "Health Wellness",
    "Education Learning Tools",
    "Customer Support",
    "Audio Processing",
    "ERP Systems",
    "Finance",
    "Browser Automation",
    "Web Scraping",
    "Monitoring",
    "Blockchain",
    "Research Data",
    "Data Platforms",
]


PLATFORM_TERMS = [
    "github", "gitlab", "bitbucket", "jira", "notion", "slack", "discord", "linear", "figma", "playwright",
    "browser", "search", "research", "sql", "postgres", "mysql", "sqlite", "mongodb", "redis", "supabase",
    "firebase", "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "stripe", "shopify", "salesforce",
    "hubspot", "zendesk", "email", "calendar", "crm", "analytics", "seo", "social", "marketing", "cms",
    "video", "audio", "image", "design", "docs", "knowledge", "memory", "rag", "vector", "security",
    "monitoring", "testing", "automation", "filesystem", "shell", "terminal", "linux", "windows", "android",
    "ios", "finance", "crypto", "blockchain", "legal", "contracts", "hotel", "travel", "maps", "education",
    "medical", "support", "customer", "project", "task", "workflow", "report", "governance",
]


def slugify(value):
    lowered = value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "skill"


def fetch_html(term):
    url = GLAMA_BASE if not term else f"{GLAMA_BASE}?query={urllib.parse.quote(term)}"
    result = subprocess.run(
        ["curl.exe", "-L", "-A", "NexraImporter/1.0", url],
        capture_output=True,
        timeout=25,
        check=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def extract_json_ld(html):
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not match:
        return None
    return json.loads(match.group(1))


def extract_search_results(document):
    for item in document.get("@graph", []):
        if item.get("@type") == "SearchResultsPage":
            return item.get("mainEntity", {}).get("itemListElement", [])
    return []


def infer_category(text, query_term):
    value = f"{query_term} {text}".lower()
    mapping = [
        ("Browser Automation", ["browser", "playwright", "web page", "webpage", "selenium"]),
        ("Code & Git", ["github", "gitlab", "repository", "repo", "pull request", "code review", "version control"]),
        ("Documentation", ["documentation", "docs", "reference", "knowledge base"]),
        ("Databases", ["database", "sql", "postgres", "mysql", "sqlite", "mongodb", "redis", "supabase", "vector"]),
        ("Communication", ["slack", "discord", "email", "chat", "messaging", "calendar"]),
        ("Project Management", ["jira", "linear", "task", "workflow", "project", "ticket", "planning"]),
        ("Design & Media", ["figma", "design", "image", "video", "audio", "multimedia"]),
        ("Cloud & DevOps", ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "monitoring", "devops"]),
        ("Security", ["security", "audit", "penetration", "vulnerability", "compliance"]),
        ("Finance & Blockchain", ["finance", "payment", "stripe", "crypto", "blockchain", "trading", "token"]),
        ("Files & Local Ops", ["file", "filesystem", "local", "shell", "terminal", "os automation"]),
        ("Business & Commerce", ["shopify", "salesforce", "hubspot", "crm", "marketing", "retail", "e-commerce"]),
        ("Research & Search", ["search", "research", "seo", "scrape", "crawl", "web scraping"]),
    ]
    for category, keywords in mapping:
        if any(keyword in value for keyword in keywords):
            return category
    return query_term if query_term else "General MCP"


def infer_functions(name, description, category, query_term):
    text = f"{name} {description} {category} {query_term}".lower()
    candidates = [
        ("browser automation", ["browser", "playwright", "webpage", "web"]),
        ("web scraping", ["scrape", "crawl", "extract"]),
        ("repository access", ["github", "gitlab", "repository", "repo"]),
        ("code review", ["code review", "static analysis", "dependency", "refactor"]),
        ("documentation lookup", ["documentation", "docs", "reference"]),
        ("database queries", ["database", "sql", "postgres", "mysql", "sqlite"]),
        ("knowledge sync", ["knowledge", "memory", "notion", "obsidian", "rag"]),
        ("messaging", ["slack", "discord", "email", "chat"]),
        ("ticket management", ["jira", "linear", "ticket", "task", "workflow", "project"]),
        ("design context", ["figma", "design", "ui"]),
        ("cloud operations", ["aws", "azure", "gcp", "kubernetes", "docker", "terraform"]),
        ("security scanning", ["security", "audit", "vulnerability", "compliance"]),
        ("payments", ["stripe", "payment", "billing"]),
        ("finance data", ["finance", "market", "trading", "crypto", "token"]),
        ("filesystem access", ["file", "filesystem", "local", "terminal", "shell"]),
        ("media generation", ["video", "audio", "image", "media"]),
        ("search", ["search", "research", "seo"]),
    ]
    functions = [label for label, keywords in candidates if any(keyword in text for keyword in keywords)]
    if not functions:
        normalized_query = slugify(query_term).replace("-", " ")
        if normalized_query:
            functions.append(normalized_query)
    if category not in functions and len(functions) < 4:
        functions.append(category.lower())
    unique_functions = []
    for item in functions:
        if item and item not in unique_functions:
            unique_functions.append(item)
    return unique_functions[:4] or ["mcp integration"]


def deterministic_metrics(url):
    digest = hashlib.sha256(url.encode("utf-8")).digest()
    price = round(0.01 + (digest[0] / 255) * 0.14, 2)
    success_rate = 82 + digest[1] % 18
    latency = 180 + digest[2] * 7
    cost_efficiency = 60 + digest[3] % 39
    user_rating_avg = round(3.6 + (digest[4] / 255) * 1.4, 1)
    user_rating_count = 10 + int.from_bytes(digest[5:7], "big") % 1800
    recent_calls = 50 + int.from_bytes(digest[7:10], "big") % 60000
    return {
        "pricePerCall": price,
        "successRate": min(success_rate, 99),
        "latencyP95": latency,
        "costEfficiency": min(cost_efficiency, 98),
        "userRatingAvg": min(user_rating_avg, 5.0),
        "userRatingCount": user_rating_count,
        "recentCalls": recent_calls,
    }


def build_skill(entry, query_term):
    item = entry.get("item", {})
    name = item.get("name", "").strip()
    description = (item.get("description") or "No description provided by source directory.").strip()
    url = item.get("url", "").strip()
    if not name or not url:
        return None

    author = item.get("author", {}).get("name", "glama-import")
    category = infer_category(f"{name} {description}", query_term)
    functions = infer_functions(name, description, category, query_term)
    metrics = deterministic_metrics(url)
    parsed_url = urllib.parse.urlparse(url)
    path_parts = [part for part in parsed_url.path.split("/") if part]
    owner_slug = slugify(path_parts[-2] if len(path_parts) >= 2 else author)
    repo_slug = slugify(path_parts[-1] if path_parts else name)
    short_hash = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]

    return {
        "id": f"skill-{owner_slug}-{repo_slug}-{short_hash}",
        "name": name,
        "category": category,
        "description": description,
        "pricePerCall": metrics["pricePerCall"],
        "status": "active",
        "successRate": metrics["successRate"],
        "latencyP95": metrics["latencyP95"],
        "costEfficiency": metrics["costEfficiency"],
        "userRatingAvg": metrics["userRatingAvg"],
        "userRatingCount": metrics["userRatingCount"],
        "recentCalls": metrics["recentCalls"],
        "functions": functions,
        "invocationMethod": "MCP server listing imported from public registry metadata",
        "submittedBy": "glama-import",
        "approvalStatus": "APPROVED",
        "source": "Glama MCP Directory",
        "sourceUrl": url,
        "sourceAuthor": author,
        "sourceQuery": query_term,
        "license": item.get("license"),
        "operatingSystem": item.get("operatingSystem"),
    }


def build_query_terms():
    letters = [chr(code) for code in range(ord("a"), ord("z") + 1)]
    double_letters = [f"{first}{second}" for first in letters for second in letters]
    return CATEGORY_TERMS + PLATFORM_TERMS + letters + double_letters


def write_outputs(skills, source_queries, failed_queries):
    skills = list(skills)
    skills.sort(key=lambda item: (-item["recentCalls"], item["name"].lower()))

    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(skills, handle, ensure_ascii=False, indent=2)

    report = {
        "source": "Glama MCP Directory",
        "sourceUrl": GLAMA_BASE,
        "generatedSkillCount": len(skills),
        "targetSkillCount": TARGET_COUNT,
        "queriesTried": len(source_queries) + len(failed_queries),
        "topSourceQueries": source_queries.most_common(50),
        "failedQueries": failed_queries[:50],
        "note": "Names, descriptions, source URLs, authors, and licenses come from the public directory pages. Rating, usage, latency, and billing-style metrics are deterministic synthetic seed values inferred for Nexra demo use because public directories do not provide Nexra-native trust telemetry.",
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)


def main():
    query_terms = build_query_terms()
    unique_skills = {}
    source_queries = Counter()
    failed_queries = []

    batch_size = 24
    max_workers = 12

    for batch_start in range(0, len(query_terms), batch_size):
        if len(unique_skills) >= TARGET_COUNT:
            break

        batch = query_terms[batch_start:batch_start + batch_size]
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_term = {executor.submit(fetch_html, term): term for term in batch}
            for future in as_completed(future_to_term):
                term = future_to_term[future]
                try:
                    html = future.result()
                    document = extract_json_ld(html)
                    if not document:
                        failed_queries.append({"query": term, "reason": "missing_json_ld"})
                        continue

                    entries = extract_search_results(document)
                    added = 0
                    for entry in entries:
                        skill = build_skill(entry, term)
                        if not skill:
                            continue
                        unique_key = skill["sourceUrl"]
                        if unique_key in unique_skills:
                            continue
                        unique_skills[unique_key] = skill
                        source_queries[term] += 1
                        added += 1

                    print(f"[{len(source_queries) + len(failed_queries)}/{len(query_terms)}] query='{term}' added={added} total={len(unique_skills)}")
                except Exception as exc:  # noqa: BLE001
                    failed_queries.append({"query": term, "reason": str(exc)})
                    print(f"query='{term}' failed={exc}", file=sys.stderr)

        write_outputs(unique_skills.values(), source_queries, failed_queries)
        print(f"checkpoint total={len(unique_skills)}")
        time.sleep(0.15)

    write_outputs(unique_skills.values(), source_queries, failed_queries)
    print(f"Wrote {len(unique_skills)} skills to {OUTPUT_PATH}")
    print(f"Wrote import report to {REPORT_PATH}")
    if len(unique_skills) < TARGET_COUNT:
        print(f"WARNING: only collected {len(unique_skills)} skills", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
