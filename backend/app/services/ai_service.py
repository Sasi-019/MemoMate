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
Use data.item_id when the user provides an identifiable item ID.

Otherwise use the available item information.

Example:

{
  "action": "COMPLETE_LIST_ITEM",
  "response": "I can mark the item as completed.",
  "data": {
    "item_id": 12
  }
}


REMOVE_LIST_ITEM
----------------
Use data.item_id when available.

Example:

{
  "action": "REMOVE_LIST_ITEM",
  "response": "I can remove that item from your list.",
  "data": {
    "item_id": 12
  }
}


CREATE_REMINDER
----------------
Required:
- data.title
- data.remind_at OR date/time information

Example:

User: "remind me to call mom tomorrow at 6 PM"

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

Example:

User: "What do I have tomorrow?"

Return:

{
  "action": "GET_NEXT_EVENT",
  "response": "I can check your upcoming schedule.",
  "data": {
    "date": "tomorrow"
  }
}


VIEW_LIST
----------------
Use when the user wants to see/list the contents of a list.

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

Keep the event information in data.


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

    # Add previous conversation.
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

    completion = client.chat.completions.create(
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