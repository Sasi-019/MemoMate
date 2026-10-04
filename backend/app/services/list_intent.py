"""
Rule-based detection of clear list commands.

Creating a list or asking "what lists do I have?" is simple enough that it
should not depend on a small language model returning perfect JSON (or on the
AI service being reachable at all). These commands are recognised here first;
anything else still goes to the AI model.
"""

import re


STRIP_CHARS = " .!?'‘’\"“”"

CREATE_VERBS = r"(?:create|make|crete|creat|new|start)"

# Words that, if captured as a "list name", really mean "no name given".
NO_NAME_WORDS = {"", "my", "the", "a", "an", "all", "every", "your", "me"}


def _clean_name(name: str) -> str:
    name = (name or "").strip(STRIP_CHARS)

    name = re.sub(
        r"\s+(?:please|now)$",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip(STRIP_CHARS)

    name = re.sub(
        r"^(?:a|an|the|my|new)\s+",
        "",
        name,
        flags=re.IGNORECASE,
    ).strip(STRIP_CHARS)

    return name


def _title(name: str) -> str:
    return name[:1].upper() + name[1:]


def detect_list_intent(message: str):
    """
    Return {"action", "response", "data"} for an obvious list command,
    or None if the message should go to the AI model.
    """

    text = (message or "").strip().strip(STRIP_CHARS)

    if not text:
        return None

    lower = text.lower()

    has_edit_verb = re.search(
        r"\b(create|make|crete|creat|new|delete|remove|add|put)\b",
        lower,
    )

    # -----------------------------------------------------
    # 1. Summary of ALL lists
    #    "show my lists", "what lists do I have",
    #    "give me a summary of my lists"
    # -----------------------------------------------------
    if re.search(r"\blists\b", lower) and not has_edit_verb:
        return {
            "action": "VIEW_LIST",
            "response": "Here is a summary of your lists.",
            "data": {},
        }

    # -----------------------------------------------------
    # 2. Create a list
    #    "create a shopping list", "crete list veg",
    #    "make a list called veg", "create list of groceries"
    # -----------------------------------------------------
    create_patterns = [
        rf"^(?:please\s+)?{CREATE_VERBS}\s+(?:a\s+|an\s+|new\s+)*list\s+"
        r"(?:of\s+name\s+|name\s+|called\s+|named\s+|of\s+|for\s+)?(.+)$",
        rf"^(?:please\s+)?{CREATE_VERBS}\s+(?:a\s+|an\s+|new\s+)*(.+?)\s+list$",
    ]

    for pattern in create_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if not match:
            continue

        name = _clean_name(match.group(1))

        # "make a note to buy milk in the kitchen list" is not a list name.
        if (
            not name
            or name.lower() in NO_NAME_WORDS
            or len(name.split()) > 6
            or re.search(r"\b(?:to|into|in)\b", name, flags=re.IGNORECASE)
        ):
            continue

        name = _title(name)

        return {
            "action": "CREATE_LIST",
            "response": f"I can create a {name} list for you.",
            "data": {"name": name},
        }

    # -----------------------------------------------------
    # 3. Show / summarise ONE list
    #    "show my shopping list", "what's in my veg list",
    #    "summary of my shopping list"
    # -----------------------------------------------------
    view_patterns = [
        r"\bsummar\w*\s+(?:of\s+)?(?:the\s+|my\s+)?(.+?)\s+list$",
        r"^(?:please\s+)?what(?:'s|\s+is|\s+are)\s+(?:in|on)\s+"
        r"(?:the\s+|my\s+)?(.+?)\s+list$",
        r"^(?:please\s+)?what\s+do\s+i\s+have\s+(?:in|on)\s+"
        r"(?:the\s+|my\s+)?(.+?)\s+list$",
        r"^(?:please\s+)?(?:show|view|see|open|display|read|give)\s+"
        r"(?:me\s+)?(?:the\s+|my\s+)?(.+?)\s+list$",
    ]

    for pattern in view_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)

        if not match:
            continue

        name = _clean_name(match.group(1))

        if len(name.split()) > 6:
            continue

        if name.lower() in NO_NAME_WORDS:
            return {
                "action": "VIEW_LIST",
                "response": "Here is a summary of your lists.",
                "data": {},
            }

        return {
            "action": "VIEW_LIST",
            "response": f"Here is your {_title(name)} list.",
            "data": {"list_name": name},
        }

    return None
