import json
import os
import re

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")
HF_MODEL = os.getenv(
    "HF_MODEL",
    "Qwen/Qwen3-4B-Instruct-2507",
)

if not HF_TOKEN:
    raise RuntimeError(
        "HF_TOKEN is missing. Add HF_TOKEN to backend/.env"
    )


# ---------------------------------------------------------
# Hugging Face client
# ---------------------------------------------------------

client = InferenceClient(
    provider="auto",
    api_key=HF_TOKEN,
)


# ---------------------------------------------------------
# System prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are MemoMate, an AI memory assistant.

Your job is to understand what the user wants and return
a structured JSON object.

MemoMate can manage:

- calendar events
- reminders
- lists
- personal memory
- schedules
- upcoming tasks

IMPORTANT:

You are currently interpreting the user's request.

Do NOT claim that an action has already been completed.

Return ONLY valid JSON.

The JSON must have exactly these fields:

{
  "action": "ACTION_NAME",
  "response": "short natural-language response",
  "data": {}
}

Allowed actions:

NONE
CREATE_EVENT
CREATE_REMINDER
CREATE_LIST
ADD_LIST_ITEM
REMOVE_LIST_ITEM
COMPLETE_LIST_ITEM
DELETE_LIST
SAVE_MEMORY
SEARCH_MEMORY
GET_NEXT_EVENT
VIEW_LIST

Examples:

User:
"Remind me to call mom tomorrow at 6 PM"

Return:

{
  "action": "CREATE_REMINDER",
  "response": "I can set a reminder to call mom tomorrow at 6 PM.",
  "data": {
    "title": "Call mom",
    "date": "tomorrow",
    "time": "18:00"
  }
}

User:
"Add milk and bread to my shopping list"

Return:

{
  "action": "ADD_LIST_ITEM",
  "response": "I can add milk and bread to your shopping list.",
  "data": {
    "list_name": "Shopping",
    "items": ["milk", "bread"]
  }
}

User:
"What do I have tomorrow?"

Return:

{
  "action": "GET_NEXT_EVENT",
  "response": "I can check your upcoming schedule.",
  "data": {
    "date": "tomorrow"
  }
}

For normal conversation:

{
  "action": "NONE",
  "response": "natural helpful response",
  "data": {}
}

Never invent that an action has already happened.
"""


# ---------------------------------------------------------
# Extract JSON from model response
# ---------------------------------------------------------

def extract_json(text: str):

    if not text:
        return None

    cleaned = text.strip()

    # Remove markdown JSON fences
    cleaned = re.sub(
        r"```json\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"```\s*",
        "",
        cleaned,
    )

    cleaned = cleaned.strip()

    # Try direct JSON parsing
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from surrounding text
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:

        possible_json = cleaned[
            start:end + 1
        ]

        try:
            return json.loads(possible_json)
        except json.JSONDecodeError:
            pass

    return None


# ---------------------------------------------------------
# Normalize model result
# ---------------------------------------------------------

def normalize_result(parsed):

    if not isinstance(parsed, dict):

        return {
            "action": "NONE",
            "response": (
                "I understood your message, "
                "but I couldn't structure the request yet."
            ),
            "data": {},
        }

    action = parsed.get(
        "action",
        "NONE",
    )

    response = parsed.get(
        "response",
    )

    data = parsed.get(
        "data",
    )

    if not isinstance(action, str):
        action = "NONE"

    if not isinstance(response, str) or not response.strip():
        response = "I understood your request."

    if not isinstance(data, dict):
        data = {}

    return {
        "action": action,
        "response": response.strip(),
        "data": data,
    }


# ---------------------------------------------------------
# Process user message
# ---------------------------------------------------------

def process_message(
    message: str,
    conversation=None,
):

    if not message or not message.strip():

        raise ValueError(
            "Message cannot be empty."
        )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    # Add previous conversation
    if conversation:

        for item in conversation[-8:]:

            role = item.get("role")
            content = item.get("content")

            if (
                role in {"user", "assistant"}
                and content
            ):

                messages.append(
                    {
                        "role": role,
                        "content": content,
                    }
                )

    # Add current message
    messages.append(
        {
            "role": "user",
            "content": message.strip(),
        }
    )

    # -----------------------------------------------------
    # Call Hugging Face
    # -----------------------------------------------------

    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=messages,
        max_tokens=500,
        temperature=0.2,
    )

    # -----------------------------------------------------
    # Read response
    # -----------------------------------------------------

    if not completion.choices:

        raise RuntimeError(
            "The AI model returned no choices."
        )

    model_message = completion.choices[0].message

    content = model_message.content

    if not content:

        raise RuntimeError(
            "The AI model returned an empty response."
        )

    # -----------------------------------------------------
    # Convert model output into structured JSON
    # -----------------------------------------------------

    parsed = extract_json(content)

    return normalize_result(parsed)