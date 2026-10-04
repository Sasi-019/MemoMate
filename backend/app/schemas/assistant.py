from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str
    content: str


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation: list[ConversationMessage] = []

    # Minutes the user's timezone is AHEAD of UTC (India = 330).
    # Needed so "tomorrow at 6 PM" means 6 PM for the user, not for the server.
    tz_offset_minutes: int = Field(default=0, ge=-840, le=840)


class AssistantResponse(BaseModel):
    action: str
    response: str
    data: dict
