from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str
    content: str


class AssistantRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation: list[ConversationMessage] = []


class AssistantResponse(BaseModel):
    action: str
    response: str
    data: dict