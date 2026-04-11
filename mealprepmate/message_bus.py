import uuid
from datetime import datetime

message_bus = {
    "ceo": [],
    "product": [],
    "engineer": [],
    "marketing": [],
    "qa": []
}

def create_message(from_agent, to_agent, message_type, payload, parent_id=None):
    return {
        "message_id": str(uuid.uuid4()),
        "from_agent": from_agent,
        "to_agent": to_agent,
        "message_type": message_type,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat(),
        "parent_message_id": parent_id
    }

def send_message(message):
    message_bus[message["to_agent"]].append(message)
    print(f"\n📩 {message['from_agent']} → {message['to_agent']}")
    print(message)

def get_messages(agent):
    msgs = message_bus[agent]
    message_bus[agent] = []
    return msgs