"""Questions API — submit a question and get the V1 answer."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AnswerView, AskRequest
from app.db.session import get_session
from app.services.reasoning import answer_question, get_answer

router = APIRouter(prefix="/questions", tags=["questions"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("", response_model=AnswerView, status_code=201)
async def ask_question(payload: AskRequest, session: SessionDep) -> AnswerView:
    """Submit a question; runs the multi-agent graph and returns the V1 answer."""
    answer_id = await answer_question(
        session, payload.text, asker=payload.asker, channel=payload.channel
    )
    answer = await get_answer(session, answer_id)
    if answer is None:  # pragma: no cover — just-created row must exist
        raise HTTPException(status_code=500, detail="answer not found after creation")
    return AnswerView.from_orm_answer(answer)


@router.get("/answers/{answer_id}", response_model=AnswerView)
async def read_answer(answer_id: int, session: SessionDep) -> AnswerView:
    """Fetch a previously generated answer by id."""
    answer = await get_answer(session, answer_id)
    if answer is None:
        raise HTTPException(status_code=404, detail="answer not found")
    return AnswerView.from_orm_answer(answer)
