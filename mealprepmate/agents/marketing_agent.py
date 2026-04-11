
import os
import json
import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from message_bus import get_messages, create_message, send_message
from llm import call_llm

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SENDGRID_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("SENDER_EMAIL")
TO_EMAIL = os.getenv("TEST_EMAIL")


def clean_llm_output(text):
    text = text.strip()

    # 🔥 Remove ```json blocks if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            if "{" in part:
                text = part
                break

    return text.strip()


def run_marketing_agent():
    messages = get_messages("marketing")

    spec = None
    pr_url = None
    slack_only = False  # Flag: are we only posting to Slack (2nd run)?

    for msg in messages:
        if msg["message_type"] == "data":
            # Check if this is a PR URL + Slack posting request (2nd run)
            if "action" in msg["payload"] and msg["payload"]["action"] == "post_slack":
                pr_url = msg["payload"].get("pr_url", "N/A")
                slack_only = True
                continue
            
            spec = msg["payload"].get("product_spec")

    if not spec and not slack_only:
        print("⚠️ Marketing Agent: No product spec received yet")
        return

    if slack_only:
        print("\n📢 Marketing Agent (Slack posting only)...")
    else:
        print("\n📢 Marketing Agent working...")

    # Defaults
    data = {
        "tagline": "Transform your life with our service",
        "description": "An innovative solution designed for you.",
        "email": {
            "subject": "Discover Our New Service",
            "body": "We're excited to introduce our new offering designed to improve your life."
        },
        "social_posts": {}
    }

    try:
        # 🔥 FIRST RUN: LLM GENERATION + EMAIL
        if not slack_only:
            # 🔥 1. STRONG PROMPT (STRICT JSON)
            result = call_llm(f"""
    You are a marketing expert.

    Return ONLY valid JSON. No explanation. No extra text.

    Format:
    {{
      "tagline": "max 10 words",
      "description": "2-3 sentences",
      "email": {{
        "subject": "string",
        "body": "professional outreach email"
      }},
      "social_posts": {{
        "twitter": "post",
        "linkedin": "post",
        "instagram": "post"
      }}
    }}

    Product:
    {spec}
    """)

            # 🔥 2. CLEAN RESPONSE
            clean = clean_llm_output(result)

            # 🔥 3. SAFE PARSING
            try:
                parsed_data = json.loads(clean)
                if isinstance(parsed_data, dict):
                    data = parsed_data
            except Exception as e:
                print("❌ JSON parse failed:", e)
                print("Raw LLM output:", result[:200])

            # 🔥 4. EXTRACT EMAIL
            subject = data.get("email", {}).get("subject", "Discover Our New Service")
            body = data.get("email", {}).get("body", "We're excited to introduce our new offering designed to improve your life.")

            # 🔥 DEBUG EMAIL DETAILS
            print(f"\n📧 EMAIL DEBUG:")
            print(f"   FROM: {FROM_EMAIL}")
            print(f"   TO: {TO_EMAIL}")
            print(f"   SENDGRID_KEY exists: {bool(SENDGRID_KEY)}")
            print(f"   Subject: {subject}")
            print(f"   Body length: {len(body)} chars")
            print(f"   Body preview: {body[:80]}...")

            # 🔥 5. SEND EMAIL
            try:
                if FROM_EMAIL and TO_EMAIL and SENDGRID_KEY:
                    print("\n🔄 Attempting to send email via SendGrid...")
                    message = Mail(
                        from_email=FROM_EMAIL,
                        to_emails=TO_EMAIL,
                        subject=subject,
                        html_content=body
                    )
                    response = SendGridAPIClient(SENDGRID_KEY).send(message)
                    print(f"✅ Email sent (HTTP {response.status_code})")
                    
                    # Check if response is 202 (success)
                    if response.status_code == 202:
                        print(f"   📬 Message queued for delivery")
                    else:
                        print(f"   ⚠️ Unexpected response code: {response.status_code}")
                        print(f"   Response headers: {response.headers}")
                else:
                    print("⚠️ Email credentials missing:")
                    print(f"   FROM_EMAIL: {FROM_EMAIL is not None}")
                    print(f"   TO_EMAIL: {TO_EMAIL is not None}")
                    print(f"   SENDGRID_KEY: {SENDGRID_KEY is not None}")
            except Exception as e:
                print(f"❌ Email failed: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
        
        else:
            print("ℹ️ Skipping LLM generation and email (already done on first run)")

        # 🔥 SLACK POSTING (Both runs)
        if pr_url and pr_url != "N/A" and SLACK_TOKEN:
            try:
                payload = {
                    "channel": "#launches",
                    "blocks": [
                        {
                            "type": "header",
                            "text": {"type": "plain_text", "text": data.get("tagline", "New Launch")}
                        },
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": data.get("description", "An exciting new offering")}
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*PR:* <{pr_url}|View PR>"},
                                {"type": "mrkdwn", "text": "*Status:* Live 🚀"}
                            ]
                        }
                    ]
                }

                requests.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
                    json=payload
                )
                print("✅ Slack message sent")
            except Exception as e:
                print("❌ Slack failed:", e)
        elif not pr_url or pr_url == "N/A":
            print("⏳ Slack posting skipped: awaiting PR URL from Engineer")
    
    except Exception as e:
        print(f"❌ Marketing Agent Error: {e}")

    # 🔥 ALWAYS SEND RESULT TO CEO (only include subject if first run)
    result_payload = {
        "tagline": data.get("tagline"),
        "description": data.get("description")
    }
    if not slack_only:
        result_payload["email_subject"] = data.get("email", {}).get("subject", "Discover Our New Service")
    
    send_message(create_message(
        "marketing",
        "ceo",
        "result",
        result_payload
    ))