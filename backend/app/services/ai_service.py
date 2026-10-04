import json
import os
import re
from datetime import datetime, timedelta

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

# ---------------------------------------------------------
# Hugging Face client (created lazily)
#
# The client used to be created at import time and raised if
# HF_TOKEN was missing, which crashed the WHOLE API (login,
# reminders, lists...) on startup. Now only the assistant fails.
# ---------------------------------------------------------

_client = None


def get_client():
    global _client

    if not HF_TOKEN:
        raise RuntimeError(
            "AI assistant is not configured: HF_TOKEN is missing "
            "on the server."
        )

    if _client is None:
        _client = InferenceClient(
            provider="auto",
            api_key=HF_TOKEN,
        )

    return _client


# ---------------------------------------------------------
# System prompt
# ---------------------------------------------------------

SYSTEM_PROMPT = """
You are MemoMate, an AI memory and productivity assistant.

Your job is to understand the user's request and return ONLY
one valid JSON object.

NEVER claim that an action has already been completed.
The backend will execute the action after your response.

The JSON format MUST ALWAYS be:

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


=========================================================
IMPORTANT ACTION DATA RULES
=========================================================

CREATE_LIST
----------------
Use this when the user wants to create a new list.

The list name MUST be placed in "data.name".

Example:

User: "create a shopping list"

Return:

{
  "action": "CREATE_LIST",
  "response": "I can create a Shopping list for you.",
  "data": {
    "name": "Shopping"
  }
}

User: "create a list called veg"

Return:

{
  "action": "CREATE_LIST",
  "response": "I can create a Veg list for you.",
  "data": {
    "name": "Veg"
  }
}

User: "make a grocery list"

Return:

{
  "action": "CREATE_LIST",
  "response": "I can create a Grocery list for you.",
  "data": {
    "name": "Grocery"
  }
}


ADD_LIST_ITEM
----------------
Use this when the user wants to add something to an existing list.

The backend accepts:
- data.list_name
- data.text

For ONE item, use "text".

Example:

User: "add milk to my shopping list"

Return:

{
  "action": "ADD_LIST_ITEM",
  "response": "I can add milk to your Shopping list.",
  "data": {
    "list_name": "Shopping",
    "text": "milk"
  }
}

For multiple items, return one item at a time only if possible.
Do NOT put an "items" array in the data.

Example:

User: "add milk and bread to my shopping list"

Return:

{
  "action": "ADD_LIST_ITEM",
  "response": "I can add milk and bread to your Shopping list.",
  "data": {
    "list_name": "Shopping",
    "text": "milk and bread"
  }
}


DELETE_LIST
----------------
Use data.list_name.

Example:

{
  "action": "DELETE_LIST",
  "response": "I can delete your Shopping list.",
  "data": {
    "list_name": "Shopping"
  }
}


COMPLETE_LIST_ITEM
----------------
You do NOT know item IDs. Identify the item by its text.

Use data.item_text (the item) and data.list_name (if the user
mentioned a list).

Example:

User: "mark milk as done in my shopping list"

{
  "action": "COMPLETE_LIST_ITEM",
  "response": "I can mark milk as completed.",
  "data": {
    "item_text": "milk",
    "list_name": "Shopping"
  }
}


REMOVE_LIST_ITEM
----------------
Same as COMPLETE_LIST_ITEM: use data.item_text and, when known,
data.list_name. Never invent item IDs.

Example:

{
  "action": "REMOVE_LIST_ITEM",
  "response": "I can remove milk from your Shopping list.",
  "data": {
    "item_text": "milk",
    "list_name": "Shopping"
  }
}


CREATE_REMINDER
----------------
Required:
- data.title
- data.remind_at

data.remind_at MUST be the user's LOCAL date and time written as
"YYYY-MM-DDTHH:MM:SS". Work it out yourself from the "Current local
date and time" message that is given to you. Resolve words such as
"tomorrow", "next Monday", "in 2 hours" into a real date.

Optional: data.description, data.recurrence_type
("none", "daily", "weekly", "monthly", "yearly").

Example (if the current local date is 2026-10-04):

User: "remind me to call mom tomorrow at 6 PM"

Return:

{
  "action": "CREATE_REMINDER",
  "response": "I can set a reminder to call mom tomorrow at 6 PM.",
  "data": {
    "title": "Call mom",
    "remind_at": "2026-10-05T18:00:00"
  }
}


SAVE_MEMORY
----------------
Required:
- data.title
- data.content

Example:

{
  "action": "SAVE_MEMORY",
  "response": "I can save that as a personal memory.",
  "data": {
    "title": "Preference",
    "content": "The user prefers vegetarian food."
  }
}


GET_NEXT_EVENT
----------------
Use when the user asks about upcoming events, tasks, schedule,
or what they have tomorrow.

data.date MUST be the local date "YYYY-MM-DD" being asked about.
Leave data.date out to get the next upcoming items.

Example (if the current local date is 2026-10-04):

User: "What do I have tomorrow?"

Return:

{
  "action": "GET_NEXT_EVENT",
  "response": "I can check your upcoming schedule.",
  "data": {
    "date": "2026-10-05"
  }
}


VIEW_LIST
----------------
Use when the user wants to see/list the contents of a list.

If the user asks for ALL their lists, or a summary/overview of their
lists, use VIEW_LIST with an EMPTY data object: {}.

Example:

{
  "action": "VIEW_LIST",
  "response": "I can show your Shopping list.",
  "data": {
    "list_name": "Shopping"
  }
}


SEARCH_MEMORY
----------------
Use when the user asks about something previously saved.

Example:

{
  "action": "SEARCH_MEMORY",
  "response": "I can search your saved memories.",
  "data": {
    "query": "vegetarian food"
  }
}


CREATE_EVENT
----------------
Use when the user explicitly wants to create a calendar event.

Required:
- data.title
- data.start_time (user's LOCAL time, "YYYY-MM-DDTHH:MM:SS")

Optional: data.end_time (same format), data.description.

Example (if the current local date is 2026-10-04):

User: "add dentist appointment on Friday at 4 pm"

{
  "action": "CREATE_EVENT",
  "response": "I can add a dentist appointment on Friday at 4 PM.",
  "data": {
    "title": "Dentist appointment",
    "start_time": "2026-10-09T16:00:00"
  }
}


=========================================================
IMPORTANT NATURAL LANGUAGE RULES
=========================================================

Understand informal and misspelled requests.

Examples:

"crete list veg"
"create list veg"
"create a list of veg"
"make veg list"
"new veg list"
"create shopping"
"make shopping list"

ALL should be interpreted as CREATE_LIST.

For example:

User: "crete list veg"

Return:

{
  "action": "CREATE_LIST",
  "response": "I can create a Veg list for you.",
  "data": {
    "name": "Veg"
  }
}


If the user says:

"create list of shopping"

interpret "shopping" as the list name.

If the user says:

"create a shopping list"

interpret "Shopping" as the list name.

Do not ask for the list name when the user's message
already contains a reasonable list name.


=========================================================
NORMAL CONVERSATION
=========================================================

For greetings or questions that do not require an action:

{
  "action": "NONE",
  "response": "natural helpful response",
  "data": {}
}


=========================================================
FINAL REQUIREMENTS
=========================================================

Return ONLY valid JSON.

Do not return Markdown.

Do not return ```json fences.

Do not explain your reasoning.

Do not add extra fields.

Never claim that an action has already happened.

The backend performs the actual action.
"""


# ---------------------------------------------------------
# Extract JSON from model response
# ---------------------------------------------------------

def extract_json(text: str):

    if not text:
        return None

    cleaned = text.strip()

    # Remove Qwen/model thinking sections if present.
    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        cleaned,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

    # Remove Markdown JSON fences.
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

    # Direct JSON.
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # JSON surrounded by additional text.
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1 and end > start:
        possible_json = cleaned[start:end + 1]

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

    action = parsed.get("action", "NONE")

    response = parsed.get("response")

    data = parsed.get("data")

    if not isinstance(action, str):
        action = "NONE"

    action = action.strip().upper()

    allowed_actions = {
        "NONE",
        "CREATE_EVENT",
        "CREATE_REMINDER",
        "CREATE_LIST",
        "ADD_LIST_ITEM",
        "REMOVE_LIST_ITEM",
        "COMPLETE_LIST_ITEM",
        "DELETE_LIST",
        "SAVE_MEMORY",
        "SEARCH_MEMORY",
        "GET_NEXT_EVENT",
        "VIEW_LIST",
    }

    if action not in allowed_actions:
        action = "NONE"

    if not isinstance(response, str) or not response.strip():
        response = "I understood your request."

    if not isinstance(data, dict):
        data = {}

    # -----------------------------------------------------
    # Normalize common LLM field variations
    # -----------------------------------------------------

    if action == "CREATE_LIST":
        name = (
            data.get("name")
            or data.get("list_name")
            or data.get("title")
            or ""
        )

        data = {
            "name": str(name).strip(),
        }

    elif action == "ADD_LIST_ITEM":
        list_name = (
            data.get("list_name")
            or data.get("name")
            or ""
        )

        text = (
            data.get("text")
            or data.get("item")
            or data.get("item_text")
            or ""
        )

        data = {
            **data,
            "list_name": str(list_name).strip(),
            "text": str(text).strip(),
        }

    elif action == "DELETE_LIST":
        list_name = (
            data.get("list_name")
            or data.get("name")
            or ""
        )

        data = {
            **data,
            "list_name": str(list_name).strip(),
        }

    elif action in {
        "COMPLETE_LIST_ITEM",
        "REMOVE_LIST_ITEM",
    }:
        item_text = (
            data.get("item_text")
            or data.get("text")
            or data.get("item")
            or ""
        )

        list_name = (
            data.get("list_name")
            or data.get("list")
            or ""
        )

        data = {
            **data,
            "item_text": str(item_text).strip(),
            "list_name": str(list_name).strip(),
        }

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
    tz_offset_minutes: int = 0,
):

    if not message or not message.strip():
        raise ValueError(
            "Message cannot be empty."
        )

    # The model has no clock. Tell it the user's local date/time so it
    # can turn "tomorrow at 6 PM" into a real timestamp.
    local_now = datetime.utcnow() + timedelta(
        minutes=tz_offset_minutes
    )

    sign = "+" if tz_offset_minutes >= 0 else "-"
    abs_minutes = abs(tz_offset_minutes)

    clock_message = (
        "Current local date and time: "
        f"{local_now.strftime('%Y-%m-%d %H:%M')} "
        f"({local_now.strftime('%A')}), "
        f"UTC{sign}{abs_minutes // 60:02d}:{abs_minutes % 60:02d}."
    )

    # ONE system message only. Many chat templates reject a second
    # system message, which would break every assistant request.
    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT + "\n\n" + clock_message,
        },
    ]

    # Add previous conversation.
    if conversation:
        seen_user = False

        for item in conversation[-8:]:

            role = item.get("role")
            content = item.get("content")

            # The chat must start with a user turn; the UI's greeting
            # ("Hi! I'm MemoMate...") is an assistant turn, so skip it.
            if role == "user":
                seen_user = True

            if role == "assistant" and not seen_user:
                continue

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

    # Add current message.
    messages.append(
        {
            "role": "user",
            "content": message.strip(),
        }
    )

    # -----------------------------------------------------
    # Call Hugging Face
    # -----------------------------------------------------

    completion = get_client().chat.completions.create(
        model=HF_MODEL,
        messages=messages,
        max_tokens=500,
        temperature=0.1,
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