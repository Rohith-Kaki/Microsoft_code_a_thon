from fastapi import APIRouter, HTTPException
from backend.round2.aptitude_engine import get_aptitude_questions, evaluate_answer
from backend.round2.dsa_engine import sample_dsa_questions
from backend.round2.scoring import aggregate_round2

router = APIRouter(prefix="/round2", tags=["round2"])


@router.get("/aptitude/{role}")
def aptitude_questions(role: str):
    return get_aptitude_questions(role)


@router.post("/aptitude/submit")
def submit_aptitude(question_id: int, answer: str):
    return evaluate_answer(question_id, answer)


@router.get("/dsa/{role}")
def dsa_questions(role: str):
    return sample_dsa_questions(role)


@router.post("/final-score")
def final_score(scores: dict, hints_used: int = 0):
    return aggregate_round2(scores, hints_used)
