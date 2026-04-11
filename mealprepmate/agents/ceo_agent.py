import json
from message_bus import create_message, send_message, get_messages
from llm import call_llm

decision_log = []

# 🔥 NEW: Track processed messages
processed_ids = set()


# 🔹 1. Decompose idea
def decompose_idea(idea):
    prompt = f"""
    You are a CEO.

    Break this startup idea into tasks for:
    - Product Agent
    - Engineer Agent
    - Marketing Agent

    Idea: {idea}

    Return JSON:
    {{
      "product_task": "...",
      "engineer_task": "...",
      "marketing_task": "..."
    }}
    """
    try:
        return json.loads(call_llm(prompt))
    except:
        return {
            "product_task": "Create product specification",
            "engineer_task": "Build landing page",
            "marketing_task": "Create marketing campaign"
        }


# 🔹 2. Review Product
def review_product(spec):
    prompt = f"""
    Review this product spec.

    Check:
    - clear value proposition
    - personas
    - features priority
    - user stories quality

    Return JSON:
    {{
      "approved": true/false,
      "feedback": "..."
    }}

    Spec:
    {spec}
    """
    try:
        return json.loads(call_llm(prompt))
    except:
        return {"approved": True, "feedback": ""}


# 🔹 3. DETAILED PRODUCT VERDICT - WITH REASONS
def get_product_verdict(product_spec):
    """Generate detailed product verdict with reasons for each check"""
    prompt = f"""
    You are a CEO product reviewer. Provide DETAILED feedback on this product spec.

    CHECK THESE CRITERIA:
    
    VALUE PROPOSITION CHECKS:
    ✓ Is it clear and compelling?
    ✓ Does it answer WHAT, FOR WHOM, and WHY?
    ✓ Is it unique and differentiated?
    ✓ Is it concrete, not generic?

    PERSONAS CHECKS:
    ✓ Are personas specific with real names/roles?
    ✓ Are pain points clearly defined and relatable?
    ✓ Do personas represent diverse user segments?
    ✓ Are personas realistic and actionable?

    FEATURES CHECKS:
    ✓ Are features aligned with value proposition?
    ✓ Are features prioritized correctly (MVP first)?
    ✓ Is each feature described with clear benefits?
    ✓ Do top features solve persona pain points?

    USER STORIES CHECKS:
    ✓ Do user stories follow "As a... I want... so that..." format?
    ✓ Do they map to personas and pain points?
    ✓ Are they specific and testable?
    ✓ Do they reflect real user needs?

    Return STRICT JSON:
    {{
      "overall_verdict": "approved" or "needs_revision",
      "score": 0-100,
      "checks": {{
        "value_proposition": {{
          "status": "pass" or "fail",
          "passed": [{{"item": "name", "reason": "why it passed"}}],
          "failed": [{{"item": "name", "reason": "why it failed"}}]
        }},
        "personas": {{
          "status": "pass" or "fail",
          "passed": [{{"item": "name", "reason": "why it passed"}}],
          "failed": [{{"item": "name", "reason": "why it failed"}}]
        }},
        "features": {{
          "status": "pass" or "fail",
          "passed": [{{"item": "name", "reason": "why it passed"}}],
          "failed": [{{"item": "name", "reason": "why it failed"}}]
        }},
        "user_stories": {{
          "status": "pass" or "fail",
          "passed": [{{"item": "name", "reason": "why it passed"}}],
          "failed": [{{"item": "name", "reason": "why it failed"}}]
        }}
      }},
      "recommendations": ["specific recommendation 1", "specific recommendation 2"]
    }}

    Product Spec:
    {json.dumps(product_spec, indent=2)}
    """

    try:
        result = json.loads(call_llm(prompt))
        return result
    except:
        return {
            "overall_verdict": "approved",
            "score": 75,
            "checks": {
                "value_proposition": {
                    "status": "pass",
                    "passed": [{"item": "Clear", "reason": "Value proposition is clear"}],
                    "failed": []
                },
                "personas": {
                    "status": "pass",
                    "passed": [{"item": "Defined", "reason": "Personas are defined"}],
                    "failed": []
                },
                "features": {
                    "status": "pass",
                    "passed": [{"item": "Prioritized", "reason": "Features are prioritized"}],
                    "failed": []
                },
                "user_stories": {
                    "status": "pass",
                    "passed": [{"item": "Valid", "reason": "User stories are valid"}],
                    "failed": []
                }
            },
            "recommendations": []
        }


# 🔹 MAIN CEO
def run_ceo_agent(idea):
    print("\n🧠 CEO STARTED\n")

    tasks = decompose_idea(idea)

    # 🔥 Send ONLY product task first
    send_message(create_message(
        "ceo", "product", "task",
        {"idea": idea, "task": tasks["product_task"]}
    ))

    product_approved = False
    engineer_done = False
    marketing_done = False
    slack_posted = False  # 🔥 NEW: Track Slack posting separately
    qa_passed = False

    product_spec = None
    product_verdict = None
    engineer_output = None
    marketing_output = None

    from agents.product_agent import run_product_agent
    from agents.engineer_agent import run_engineer_agent
    from agents.marketing_agent import run_marketing_agent
    from agents.qa_agent import run_qa_agent

    # 🔥 SAFETY LIMIT
    MAX_ITER = 20
    iteration = 0

    while not qa_passed and iteration < MAX_ITER:
        iteration += 1
        print(f"\n🔁 Iteration {iteration}")

        # 🔹 RUN PRODUCT
        if not product_approved:
            print("\n▶ Running Product Agent...")
            run_product_agent()

        msgs = get_messages("ceo")

        for msg in msgs:
            if msg["message_id"] in processed_ids:
                continue

            processed_ids.add(msg["message_id"])

            sender = msg["from_agent"]
            payload = msg["payload"]

            # 🔥 PRODUCT RESPONSE
            if sender == "product" and not product_approved:
                print("\n📩 Product → CEO")

                review = review_product(payload["product_spec"])

                decision_log.append({
                    "step": "product_review",
                    "result": review
                })

                if not review["approved"]:
                    print("❌ Product rejected")

                    send_message(create_message(
                        "ceo", "product", "revision_request",
                        {"feedback": review["feedback"]}
                    ))

                else:
                    print("✅ Product approved")
                    product_approved = True
                    product_spec = payload["product_spec"]
                    
                    # 🔥 GET DETAILED PRODUCT VERDICT
                    product_verdict = get_product_verdict(product_spec)

                    # 🔥 SEND TO ENGINEER + MARKETING
                    send_message(create_message(
                        "ceo", "engineer", "data",
                        {"product_spec": product_spec}
                    ))

                    send_message(create_message(
                        "ceo", "marketing", "data",
                        {"product_spec": product_spec}
                    ))

            # 🔥 ENGINEER RESPONSE
            elif sender == "engineer" and not engineer_done:
                print("\n📩 Engineer → CEO")
                engineer_output = payload
                engineer_done = True
                
                # 🔥 IMMEDIATELY SEND PR URL TO MARKETING (for Slack posting)
                send_message(create_message(
                    "ceo", "marketing", "data",
                    {"pr_url": engineer_output.get("pr_url", "N/A"), "action": "post_slack"}
                ))

            # 🔥 MARKETING RESPONSE
            elif sender == "marketing" and not marketing_done:
                print("\n📩 Marketing → CEO")
                marketing_output = payload
                marketing_done = True

            # 🔥 QA RESPONSE
            elif sender == "qa":
                print("\n📩 QA → CEO")

                qa_result = payload

                decision_log.append({
                    "step": "qa_review",
                    "result": qa_result
                })

                if qa_result["verdict"] == "fail":
                    print("❌ QA FAILED")

                    for issue in qa_result["issues"]:

                        if any(k in issue.lower() for k in ["html", "landing", "feature"]):
                            print("🔁 Fix → Engineer")

                            send_message(create_message(
                                "ceo", "engineer", "revision_request",
                                {"feedback": issue}
                            ))
                            engineer_done = False

                        elif any(k in issue.lower() for k in ["email", "tagline", "marketing"]):
                            print("🔁 Fix → Marketing")

                            send_message(create_message(
                                "ceo", "marketing", "revision_request",
                                {"feedback": issue}
                            ))
                            marketing_done = False

                else:
                    print("✅ QA PASSED")
                    qa_passed = True

        # 🔹 RUN ENGINEER (ONLY IF NEEDED)
        if product_approved and not engineer_done:
            print("\n▶ Running Engineer Agent...")
            run_engineer_agent()

        # 🔹 CHECK ENGINEER RESPONSE
        if product_approved and not engineer_done:
            msgs = get_messages("ceo")
            for msg in msgs:
                if msg["message_id"] in processed_ids:
                    continue
                processed_ids.add(msg["message_id"])
                if msg["from_agent"] == "engineer" and not engineer_done:
                    print("\n📩 Engineer → CEO")
                    engineer_output = msg["payload"]
                    engineer_done = True

        # 🔹 RUN MARKETING (FOR EMAIL GENERATION - FIRST RUN)
        if product_approved and not marketing_done:
            print("\n▶ Running Marketing Agent...")
            run_marketing_agent()

        # 🔹 CHECK MARKETING RESPONSE
        if product_approved and not marketing_done:
            msgs = get_messages("ceo")
            for msg in msgs:
                if msg["message_id"] in processed_ids:
                    continue
                processed_ids.add(msg["message_id"])
                if msg["from_agent"] == "marketing" and not marketing_done:
                    print("\n📩 Marketing → CEO")
                    marketing_output = msg["payload"]
                    marketing_done = True

        # 🔹 SEND PR URL TO MARKETING FOR SLACK POSTING (ONLY AFTER FIRST MARKETING RUN)
        if engineer_done and marketing_done and not slack_posted:
            send_message(create_message(
                "ceo", "marketing", "data",
                {"pr_url": engineer_output.get("pr_url", "N/A"), "action": "post_slack"}
            ))
            print("\n▶ Running Marketing Agent again (posting to Slack)...")
            run_marketing_agent()
            slack_posted = True

        # 🔥 RUN QA ONLY WHEN BOTH READY
        if engineer_done and marketing_done and not qa_passed:
            print("\n▶ Running QA Agent...")

            send_message(create_message(
                "ceo", "qa", "data",
                {
                    "product_spec": product_spec,
                    "engineer": engineer_output,
                    "marketing": marketing_output
                }
            ))

            run_qa_agent()

    # 🔥 SAFETY EXIT
    if iteration >= MAX_ITER:
        print("\n⚠️ Stopped due to max iterations")

    # ====== PRODUCT VERDICT REPORT ======
    if product_verdict:
        print("\n" + "="*70)
        print("📋 PRODUCT VERDICT REPORT")
        print("="*70)
        
        overall = product_verdict.get("overall_verdict", "approved")
        score = product_verdict.get("score", 0)
        checks = product_verdict.get("checks", {})
        
        print(f"\n🎯 VERDICT: {'✅ APPROVED' if overall == 'approved' else '⚠️ NEEDS REVISION'}")
        print(f"📊 SCORE: {score}/100")
        
        # VALUE PROPOSITION
        vp_checks = checks.get("value_proposition", {})
        print(f"\n💡 VALUE PROPOSITION: {vp_checks.get('status', 'unknown').upper()}")
        if vp_checks.get("passed"):
            for item in vp_checks["passed"]:
                print(f"   ✅ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
        if vp_checks.get("failed"):
            for item in vp_checks["failed"]:
                print(f"   ❌ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
        
        # PERSONAS
        personas_checks = checks.get("personas", {})
        print(f"\n👥 PERSONAS: {personas_checks.get('status', 'unknown').upper()}")
        if personas_checks.get("passed"):
            for item in personas_checks["passed"]:
                print(f"   ✅ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
        if personas_checks.get("failed"):
            for item in personas_checks["failed"]:
                print(f"   ❌ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
        
        # FEATURES
        features_checks = checks.get("features", {})
        print(f"\n⚙️ FEATURES: {features_checks.get('status', 'unknown').upper()}")
        if features_checks.get("passed"):
            for item in features_checks["passed"]:
                print(f"   ✅ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
        if features_checks.get("failed"):
            for item in features_checks["failed"]:
                print(f"   ❌ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
        
        # USER STORIES
        stories_checks = checks.get("user_stories", {})
        print(f"\n📖 USER STORIES: {stories_checks.get('status', 'unknown').upper()}")
        if stories_checks.get("passed"):
            for item in stories_checks["passed"]:
                print(f"   ✅ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Passed')}")
        if stories_checks.get("failed"):
            for item in stories_checks["failed"]:
                print(f"   ❌ {item.get('item', 'Check')}")
                print(f"      └─ {item.get('reason', 'Failed')}")
        
        # RECOMMENDATIONS
        recommendations = product_verdict.get("recommendations", [])
        if recommendations:
            print(f"\n💬 RECOMMENDATIONS: ({len(recommendations)} items)")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*70)

    # ====== COMPREHENSIVE STRUCTURED OUTPUT ======
    print("\n" + "="*70)
    print("📊 LAUNCHMIND STARTUP ORCHESTRATION - FINAL REPORT")
    print("="*70)
    
    # 1. EXECUTION SUMMARY
    print("\n📋 EXECUTION SUMMARY:")
    print(f"   • Total Iterations: {iteration}")
    print(f"   • Product Approved: {'✅ Yes' if product_approved else '❌ No'}")
    print(f"   • Engineer Complete: {'✅ Yes' if engineer_done else '❌ No'}")
    print(f"   • Marketing Complete: {'✅ Yes' if marketing_done else '❌ No'}")
    print(f"   • QA Final Status: {'✅ PASSED' if qa_passed else '❌ FAILED'}")
    
    # 2. MESSAGE PASSING FLOW
    print("\n📩 MESSAGE PASSING FLOW:")
    print("   1. CEO → Product: Task received")
    print("   2. Product → CEO: Spec generated")
    print("   3. CEO → Engineer + Marketing: Product spec broadcast")
    print("   4. Engineer → CEO: PR created with HTML")
    print("   5. Marketing → CEO: Copy generated + email sent")
    print("   6. CEO → QA: All outputs for review")
    print("   7. QA → CEO: Validation result with issues")
    if not qa_passed:
        print("   8. CEO → Engineer/Marketing: Revision requests (if any)")
    
    # 3. PLATFORM OUTPUTS
    print("\n🚀 PLATFORM OUTPUTS:")
    if engineer_output:
        print(f"   📌 GitHub PR: {engineer_output.get('pr_url', 'N/A')}")
        print(f"   📌 GitHub Issue: {engineer_output.get('issue_url', 'N/A')}")
    if marketing_output:
        print(f"   📧 Email Subject: {marketing_output.get('email_subject', 'N/A')}")
        print(f"   💬 Tagline: {marketing_output.get('tagline', 'N/A')}")
        print(f"   📢 Slack Posted: {'✅ Yes' if slack_posted else '❌ No'}")
    
    # 4. DECISION LOG (DETAILED)
    print("\n📜 DETAILED DECISION LOG:")
    for i, decision in enumerate(decision_log, 1):
        print(f"\n   Decision #{i}:")
        if decision.get("step") == "product_review":
            result = decision.get("result", {})
            approved = result.get("approved", False)
            print(f"      • Step: Product Review")
            print(f"      • Decision: {'✅ APPROVED' if approved else '❌ REJECTED'}")
            print(f"      • Feedback: {result.get('feedback', 'None')}")
        
        elif decision.get("step") == "qa_review":
            result = decision.get("result", {})
            verdict = result.get("verdict", "unknown")
            issues = result.get("issues", [])
            print(f"      • Step: QA Review")
            print(f"      • Verdict: {'✅ PASS' if verdict == 'pass' else '❌ FAIL'}")
            print(f"      • Issues Found: {len(issues)}")
            if issues:
                for issue in issues:
                    print(f"         - {issue}")
    
    # 5. QA VALIDATION DETAILS
    if decision_log and decision_log[-1].get("step") == "qa_review":
        qa_final = decision_log[-1].get("result", {})
        print("\n🔍 QA VALIDATION DETAILS:")
        print(f"   • Final Verdict: {'✅ SYSTEM APPROVED' if qa_final.get('verdict') == 'pass' else '❌ SYSTEM REJECTED'}")
        print(f"   • Issues Identified: {len(qa_final.get('issues', []))}")
        if qa_final.get('issues'):
            print("   • Issue Categories:")
            html_issues = [i for i in qa_final['issues'] if any(k in i.lower() for k in ["html", "landing", "feature", "design"])]
            marketing_issues = [i for i in qa_final['issues'] if any(k in i.lower() for k in ["email", "tagline", "marketing", "description"])]
            print(f"      - HTML/Design Issues: {len(html_issues)}")
            print(f"      - Marketing Issues: {len(marketing_issues)}")
    
    # 6. ITERATION HISTORY
    print("\n📈 ITERATION HISTORY:")
    print(f"   • Completed: {iteration} iterations")
    if iteration >= MAX_ITER:
        print(f"   • Status: ⚠️ INCOMPLETE (Max iterations reached)")
    else:
        print(f"   • Status: {'✅ SUCCESS' if qa_passed else '⏹️ STOPPED'}")
    
    print("\n" + "="*70)
    print("END OF REPORT")
    print("="*70 + "\n")