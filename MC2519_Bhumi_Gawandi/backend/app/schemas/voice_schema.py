from pydantic import BaseModel, Field


class VoiceExpenseRequest(BaseModel):

    transcript: str = Field(
        ...,
        min_length=1,
        description="Text produced by browser speech recognition."
    )


class VoiceExpenseResponse(BaseModel):

    success: bool = True

    data: dict