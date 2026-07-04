from fastapi import HTTPException


def validate_question(
    question: str
):

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )

    if len(question.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Question too short"
        )

    if len(question) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Question exceeds maximum length"
        )

    return True