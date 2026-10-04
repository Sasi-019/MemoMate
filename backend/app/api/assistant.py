from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.ai_service import process_message
from app.services.action_engine import execute_action


router = APIRouter(
    prefix="/assistant",
    tags=["AI Assistant"],
)


@router.post("/chat", response_model=AssistantResponse)
def assistant_chat(
    request: AssistantRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Process an AI assistant message for the authenticated user.

    The LLM determines the intended action. The action engine executes
    that action using the current user's user_id so data remains isolated.
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

        action = result.get("action", "NONE")
        data = result.get("data", {})

        if action != "NONE":
            execution = execute_action(
                action=action,
                data=data,
                db=db,
                user_id=current_user.id,
            )

            result["response"] = execution.get(
                "message",
                result.get("response", ""),
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
        print("\n========== AI ERROR ==========")
        print(type(exc).__name__)
        print(str(exc))
        print("==============================\n")

        raise HTTPException(
            status_code=500,
            detail="AI assistant failed to process the request.",
        )
