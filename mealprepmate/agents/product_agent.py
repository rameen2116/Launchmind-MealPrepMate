import json
from message_bus import get_messages, create_message, send_message
from llm import call_llm


def generate_product_spec(idea, feedback=None):
    """Generate product spec using LLM with error handling and retries"""
    
    feedback_context = ""
    if feedback:
        feedback_context = f"\n\nPREVIOUS FEEDBACK TO ADDRESS:\n{feedback}\n"
    
    prompt = f"""You are an expert product manager. Create a detailed product specification.

STARTUP IDEA:
{idea}
{feedback_context}

Generate a comprehensive product specification with:
1. A clear, compelling value proposition (1 sentence)
2. Three distinct user personas with specific names, roles, and pain points
3. Five core features ranked by priority with descriptions
4. Three user stories in "As a [user], I want [action] so that [benefit]" format

Return ONLY valid JSON:
{{
  "value_proposition": "one sentence describing what, for whom, and why",
  "personas": [
    {{
      "name": "specific name",
      "role": "job title or role",
      "pain_point": "specific problem they face"
    }}
  ],
  "features": [
    {{
      "name": "feature name",
      "description": "what it does and why it matters",
      "priority": 1
    }}
  ],
  "user_stories": ["As a X, I want Y so that Z"]
}}

Be specific to this idea. Do not use generic examples.
"""
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = call_llm(prompt)
            
            # Try to extract JSON
            if "```" in result:
                start = result.find("{")
                end = result.rfind("}") + 1
                if start >= 0 and end > start:
                    result = result[start:end]
            
            spec = json.loads(result)
            
            # Validate structure
            if all(k in spec for k in ["value_proposition", "personas", "features", "user_stories"]):
                if len(spec["personas"]) >= 2 and len(spec["features"]) >= 3:
                    return spec, None
        
        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error (attempt {attempt+1}/{max_retries}): {str(e)}"
            print(f"⚠️ {error_msg}")
            if attempt == max_retries - 1:
                return None, error_msg
        
        except Exception as e:
            error_msg = f"LLM error (attempt {attempt+1}/{max_retries}): {str(e)}"
            print(f"⚠️ {error_msg}")
            if attempt == max_retries - 1:
                return None, error_msg
    
    return None, "Failed to generate valid product spec after retries"


def run_product_agent():
    messages = get_messages("product")

    for msg in messages:
        if msg["message_type"] == "task":
            idea = msg["payload"]["idea"]
            print("\n🎯 Product Agent: Generating spec...")
            
            spec, error = generate_product_spec(idea)
            
            if error:
                print(f"❌ Product Generation Failed: {error}")
                send_message(create_message(
                    "product", "ceo", "result",
                    {"status": "failed", "error": error}
                ))
                return
            
            print("✅ Product spec generated successfully")
            
            # 🔥 DISPLAY SPEC DETAILS
            print("\n" + "="*60)
            print("📋 PRODUCT SPECIFICATION")
            print("="*60)
            print(f"\n💡 VALUE PROPOSITION:")
            print(f"   {spec.get('value_proposition', 'N/A')}")
            
            print(f"\n👥 USER PERSONAS ({len(spec.get('personas', []))}):")
            for persona in spec.get("personas", []):
                print(f"   • {persona.get('name', 'Unknown')} ({persona.get('role', 'Unknown')})")
                print(f"     Pain Point: {persona.get('pain_point', 'N/A')}")
            
            print(f"\n⭐ KEY FEATURES ({len(spec.get('features', []))}):")
            for feature in spec.get("features", []):
                print(f"   {feature.get('priority', '?')}. {feature.get('name', 'Unknown')}")
                print(f"      {feature.get('description', 'N/A')}")
            
            print(f"\n📖 USER STORIES:")
            for story in spec.get("user_stories", []):
                print(f"   • {story}")
            print("\n" + "="*60)

            # 🔥 SEND TO ENGINEER
            send_message(create_message(
                "product", "engineer", "data",
                {"product_spec": spec}
            ))

            # 🔥 SEND TO MARKETING
            send_message(create_message(
                "product", "marketing", "data",
                {"product_spec": spec}
            ))

            # 🔥 CONFIRM TO CEO
            send_message(create_message(
                "product", "ceo", "result",
                {"product_spec": spec, "status": "product_spec_ready"}
            ))
        
        elif msg["message_type"] == "revision_request":
            idea = msg["payload"].get("idea", "")
            feedback = msg["payload"].get("feedback", "")
            print(f"\n🔄 Product Agent: Revision requested - {feedback}")
            
            spec, error = generate_product_spec(idea, feedback)
            
            if error:
                print(f"❌ Product Revision Failed: {error}")
                send_message(create_message(
                    "product", "ceo", "result",
                    {"status": "revision_failed", "error": error},
                    parent_id=msg["message_id"]
                ))
                return
            
            print("✅ Product spec revised")
            
            # Send revised spec
            send_message(create_message(
                "product", "engineer", "data",
                {"product_spec": spec}
            ))
            send_message(create_message(
                "product", "marketing", "data",
                {"product_spec": spec}
            ))
            send_message(create_message(
                "product", "ceo", "result",
                {"product_spec": spec, "status": "revision_complete"},
                parent_id=msg["message_id"]
            ))