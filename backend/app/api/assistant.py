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

    Extracts missing list names/items from natural-language
    requests so small LLM formatting differences do not break
    list creation or item management.
    """

    text = (message or "").strip()
    lower = text.lower()

    action = result.get("action", "NONE")
    data = result.get("data") or {}

    if not isinstance(data, dict):
        data = {}

    # =========================================================
    # CREATE LIST
    # =========================================================

    if action == "CREATE_LIST":

        name = (
            data.get("name")
            or data.get("list_name")
            or data.get("list")
            or data.get("title")
        )

        if not name:

            patterns = [
                # create list of name veg
                r"(?:create|make|new|crete)\s+(?:a\s+)?list\s+of\s+name\s+(.+)",

                # create list name veg
                r"(?:create|make|new|crete)\s+(?:a\s+)?list\s+name\s+(.+)",

                # create a list called shopping
                r"(?:create|make|new|crete)\s+(?:a\s+)?list\s+(?:called|named)\s+(.+)",

                # create a list of shopping
                r"(?:create|make|new|crete)\s+(?:a\s+)?list\s+(?:of|for)\s+(.+)",

                # create shopping list
                r"(?:create|make|new|crete)\s+(?:a\s+)?(.+?)\s+list$",
            ]

            for pattern in patterns:
                match = re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                if match:
                    name = match.group(1).strip()
                    break

        if name:
            name = str(name).strip(
                " .!?'\u2018\u2019\"\u201c\u201d"
            )

            # Remove accidental trailing words caused by
            # natural-language phrasing.
            name = re.sub(
                r"\s+(?:please|now)$",
                "",
                name,
                flags=re.IGNORECASE,
            ).strip()

            if name:
                data["name"] = name

    # =========================================================
    # ADD LIST ITEM
    # =========================================================

    elif action == "ADD_LIST_ITEM":

        list_name = (
            data.get("list_name")
            or data.get("list")
            or data.get("name")
        )

        item_text = (
            data.get("text")
            or data.get("item")
            or data.get("item_text")
        )

        if not list_name:

            patterns = [
                # add milk to my shopping list
                r"(?:to|into|in)\s+(?:my\s+)?(.+?)\s+list\b",

                # add milk to shopping
                r"(?:to|into|in)\s+(?:my\s+)?(.+?)$",
            ]

            for pattern in patterns:
                match = re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                if match:
                    list_name = match.group(1).strip()
                    break

        if not item_text:

            match = re.search(
                r"(?:add|put)\s+(.+?)\s+(?:to|into|in)\s+",
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

    # =========================================================
    # DELETE LIST
    # =========================================================

    elif action == "DELETE_LIST":

        name = (
            data.get("name")
            or data.get("list_name")
            or data.get("list")
        )

        if not name:

            patterns = [
                r"(?:delete|remove)\s+(?:my\s+)?(.+?)\s+list\b",
                r"(?:delete|remove)\s+(?:the\s+)?list\s+(?:called|named)\s+(.+)",
            ]

            for pattern in patterns:
                match = re.search(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )

                if match:
                    name = match.group(1).strip()
                    break

        if name:
            data["name"] = str(
                name
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
            tz_offset_minutes=request.tz_offset_minutes,
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
                tz_offset_minutes=request.tz_offset_minutes,
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

    except RuntimeError as exc:
        # e.g. HF_TOKEN missing, or the model returned nothing.
        print("[MemoMate AI Error]", str(exc))

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

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
            )
        )