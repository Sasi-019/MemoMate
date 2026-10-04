import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.assistant import (
    AssistantRequest,
    AssistantResponse,
)
from app.services.ai_service import process_message
from app.services.action_engine import execute_action


router = APIRouter(
    prefix="/assistant",
    tags=["AI Assistant"],
)


def normalize_list_action(message: str, result: dict) -> dict:
    """
    Repair common LLM outputs for Smart Lists.

    The model may correctly identify CREATE_LIST / ADD_LIST_ITEM
    but occasionally omit the structured parameter. This extracts
    the missing value from the user's natural-language request.
    """

    text = (message or "").strip()

    action = result.get("action", "NONE")
    data = result.get("data") or {}

    if not isinstance(data, dict):
        data = {}

    lower = text.lower()

    # ---------------------------------------------------------
    # CREATE LIST
    # ---------------------------------------------------------

    if action == "CREATE_LIST":
        name = (
            data.get("name")
            or data.get("list_name")
            or data.get("list")
        )

        if not name:
            patterns = [
                r"create\s+(?:a\s+)?list\s+(?:of|for|named|called)\s+(.+)",
                r"make\s+(?:a\s+)?list\s+(?:of|for|named|called)\s+(.+)",
                r"new\s+list\s+(?:of|for|named|called)\s+(.+)",
                r"create\s+(?:a\s+)?(.+?)\s+list",
                r"make\s+(?:a\s+)?(.+?)\s+list",
            ]

            for pattern in patterns:
                match = re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                if match:
                    name = match.group(1)
                    break

        if name:
            name = str(name).strip(
                " .!?'\u2018\u2019\"\u201c\u201d"
            )

            data["name"] = name

    # ---------------------------------------------------------
    # ADD LIST ITEM
    # ---------------------------------------------------------

    if action == "ADD_LIST_ITEM":
        list_name = (
            data.get("list_name")
            or data.get("list")
        )

        item_text = (
            data.get("text")
            or data.get("item")
        )

        if not list_name:
            match = re.search(
                r"(?:to|into|in)\s+(?:my\s+)?(.+?)\s+list\b",
                text,
                flags=re.IGNORECASE,
            )

            if match:
                list_name = match.group(1).strip()

        if not item_text:
            match = re.search(
                r"add\s+(.+?)\s+(?:to|into|in)\s+(?:my\s+)?",
                text,
                flags=re.IGNORECASE,
            )

            if match:
                item_text = match.group(1).strip()

        if list_name:
            data["list_name"] = str(
                list_name
            ).strip(
                " .!?'\u2018\u2019\"\u201c\u201d"
            )

        if item_text:
            data["text"] = str(
                item_text
            ).strip(
                " .!?'\u2018\u2019\"\u201c\u201d"
            )

    result["data"] = data

    return result


@router.post(
    "/chat",
    response_model=AssistantResponse,
)
def assistant_chat(
    request: AssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process an AI assistant message for the authenticated user.

    The LLM determines the intended action. The action engine
    executes that action using the current user's user_id.
    """

    try:
        conversation = [
            item.model_dump()
            for item in request.conversation
        ]

        result = process_message(
            request.message,
            conversation,
        )

        result = normalize_list_action(
            request.message,
            result,
        )

        action = result.get(
            "action",
            "NONE",
        )

        data = result.get(
            "data",
            {},
        )

        if action != "NONE":
            execution = execute_action(
                action=action,
                data=data,
                db=db,
                user_id=current_user.id,
            )

            result["response"] = execution.get(
                "message",
                result.get(
                    "response",
                    "",
                ),
            )

            result["data"] = {
                **data,
                "execution": execution,
            }

        return result

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "\n========== AI ERROR =========="
        )
        print(type(exc).__name__)
        print(str(exc))
        print(
            "==============================\n"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "AI assistant failed to "
                "process the request."
            ),
        )