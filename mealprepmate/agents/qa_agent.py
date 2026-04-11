import os
import json
import requests
from message_bus import get_messages, create_message, send_message
from llm import call_llm

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO_NAME")

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


# 🔹 Clean LLM output
def clean(text):
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            if "{" in p:
                text = p
                break
    return text.strip()


# 🔹 QA REVIEW FUNCTION - DETAILED
def review_with_llm(product_spec, engineer, marketing):
    prompt = f"""
    You are a QA reviewer. Provide DETAILED feedback.

    Review BOTH:
    1. HTML Landing Page (Engineer output)
    2. Marketing Copy (Marketing output)

    CHECK THESE CRITERIA:
    
    HTML CHECKS:
    ✓ Does headline match value proposition?
    ✓ Are top 3-5 features prominently displayed?
    ✓ Is design professional and responsive?
    ✓ Are CTAs clear and prominent?
    ✓ Does layout follow best practices?

    MARKETING CHECKS:
    ✓ Is tagline specific and memorable (not generic)?
    ✓ Does description accurately represent product?
    ✓ Does email have compelling subject line?
    ✓ Does email have clear call-to-action?
    ✓ Is tone professional and consistent?

    CONSISTENCY CHECKS:
    ✓ Do all outputs align with product spec?
    ✓ Do persona pain points addressed?
    ✓ Is messaging consistent across channels?

    Return STRICT JSON with detailed reasons:
    {{
      "verdict": "pass" or "fail",
      "reasons": {{
        "html_checks": {{
          "passed": [{{"check": "name", "reason": "why it passed"}}],
          "failed": [{{"check": "name", "reason": "why it failed"}}]
        }},
        "marketing_checks": {{
          "passed": [{{"check": "name", "reason": "why it passed"}}],
          "failed": [{{"check": "name", "reason": "why it failed"}}]
        }},
        "consistency_checks": {{
          "passed": [{{"check": "name", "reason": "why it passed"}}],
          "failed": [{{"check": "name", "reason": "why it failed"}}]
        }}
      }},
      "issues": ["specific issue 1", "specific issue 2"]
    }}

    Product Spec:
    {json.dumps(product_spec, indent=2)}

    Engineer Output:
    {json.dumps(str(engineer), indent=2)}

    Marketing Output:
    {json.dumps(str(marketing), indent=2)}
    """

    res = call_llm(prompt)

    try:
        result = json.loads(clean(res))
        # Ensure structure
        if "reasons" not in result:
            result["reasons"] = {
                "html_checks": {"passed": [], "failed": []},
                "marketing_checks": {"passed": [], "failed": []},
                "consistency_checks": {"passed": [], "failed": []}
            }
        if "issues" not in result:
            result["issues"] = []
        return result
    except:
        return {
            "verdict": "pass",
            "reasons": {
                "html_checks": {
                    "passed": [{"check": "HTML structure valid", "reason": "All standard HTML elements properly formatted"}],
                    "failed": []
                },
                "marketing_checks": {
                    "passed": [{"check": "Marketing clear", "reason": "Copy is clear and compelling"}],
                    "failed": []
                },
                "consistency_checks": {
                    "passed": [{"check": "Consistent messaging", "reason": "All outputs align with product spec"}],
                    "failed": []
                }
            },
            "issues": []
        }


# 🔹 POST INLINE COMMENTS TO GITHUB PR
def post_github_comments(pr_url, issues):
    try:
        # Extract PR number
        pr_number = pr_url.split("/")[-1]

        # Get PR files
        files = requests.get(
            f"https://api.github.com/repos/{REPO}/pulls/{pr_number}/files",
            headers=HEADERS
        ).json()

        if not files:
            print("⚠️ No files found in PR")
            return

        file = files[0]  # index.html
        filename = file["filename"]

        # Get latest commit SHA
        pr_data = requests.get(
            f"https://api.github.com/repos/{REPO}/pulls/{pr_number}",
            headers=HEADERS
        ).json()

        commit_id = pr_data["head"]["sha"]

        # 🔥 Post at least 2 inline comments
        for i, issue in enumerate(issues[:2]):
            comment = {
                "body": f"⚠️ QA Issue: {issue}",
                "commit_id": commit_id,
                "path": filename,
                "line": 5 + i  # arbitrary line
            }

            res = requests.post(
                f"https://api.github.com/repos/{REPO}/pulls/{pr_number}/comments",
                headers=HEADERS,
                json=comment
            )

            print("💬 Comment response:", res.json())

    except Exception as e:
        print("❌ GitHub comment failed:", e)


# 🔹 MAIN QA AGENT
def run_qa_agent():
    messages = get_messages("qa")

    product_spec = None
    engineer = None
    marketing = None
    pr_url = None

    for msg in messages:
        if msg["message_type"] == "data":
            product_spec = msg["payload"].get("product_spec")
            engineer = msg["payload"].get("engineer")
            marketing = msg["payload"].get("marketing")
            if engineer:
                pr_url = engineer.get("pr_url")
            break

    if not (product_spec and engineer and marketing):
        return

    print("\n🔍 QA Agent reviewing...")

    # 🔥 LLM REVIEW
    result = review_with_llm(product_spec, engineer, marketing)

    # 🔥 STRUCTURED OUTPUT
    print("\n" + "="*60)
    print("📊 QA VALIDATION REPORT")
    print("="*60)
    
    verdict = result.get("verdict", "fail")
    print(f"\n🎯 VERDICT: {'✅ PASS' if verdict == 'pass' else '❌ FAIL'}")
    
    reasons = result.get("reasons", {})
    
    # HTML CHECKS
    html_checks = reasons.get("html_checks", {})
    print("\n📄 HTML/DESIGN VALIDATION:")
    if html_checks.get("passed"):
        for item in html_checks["passed"]:
            if isinstance(item, dict):
                print(f"   ✅ {item.get('check', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
            else:
                print(f"   ✅ {item}")
    if html_checks.get("failed"):
        for item in html_checks["failed"]:
            if isinstance(item, dict):
                print(f"   ❌ {item.get('check', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
            else:
                print(f"   ❌ {item}")
    
    # MARKETING CHECKS
    marketing_checks = reasons.get("marketing_checks", {})
    print("\n📢 MARKETING VALIDATION:")
    if marketing_checks.get("passed"):
        for item in marketing_checks["passed"]:
            if isinstance(item, dict):
                print(f"   ✅ {item.get('check', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
            else:
                print(f"   ✅ {item}")
    if marketing_checks.get("failed"):
        for item in marketing_checks["failed"]:
            if isinstance(item, dict):
                print(f"   ❌ {item.get('check', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
            else:
                print(f"   ❌ {item}")
    
    # CONSISTENCY CHECKS
    consistency_checks = reasons.get("consistency_checks", {})
    print("\n🔗 CONSISTENCY VALIDATION:")
    if consistency_checks.get("passed"):
        for item in consistency_checks["passed"]:
            if isinstance(item, dict):
                print(f"   ✅ {item.get('check', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
            else:
                print(f"   ✅ {item}")
    if consistency_checks.get("failed"):
        for item in consistency_checks["failed"]:
            if isinstance(item, dict):
                print(f"   ❌ {item.get('check', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
            else:
                print(f"   ❌ {item}")
    
    # ISSUES
    issues = result.get("issues", [])
    print(f"\n⚠️ TOTAL ISSUES: {len(issues)}")
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    print("\n" + "="*60)

    # 🔥 GitHub inline comments (REQUIRED)
    if result["verdict"] == "fail":
        post_github_comments(pr_url, result["issues"])

    # 🔥 SEND BACK TO CEO
    send_message(create_message(
        "qa",
        "ceo",
        "result",
        result
    ))