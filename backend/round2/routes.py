from fastapi import APIRouter, HTTPException, Form
from backend.round2.aptitude_engine import get_aptitude_questions, evaluate_answer
from backend.round2.dsa_engine import sample_dsa_questions
from backend.round2.scoring import aggregate_round2
from backend.round2 import service as r2service

router = APIRouter(prefix="/round2", tags=["round2"])


@router.get("/start/{application_id}")
def start_round(application_id: int):
    try:
        return r2service.start_round2(application_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="application not found")


@router.get("/aptitude/{role}")
def aptitude_questions(role: str):
    return get_aptitude_questions(role)


@router.post("/aptitude/submit")
def submit_aptitude(question_id: int = Form(...), answer: str = Form(...), application_id: int | None = Form(None)):
    res = evaluate_answer(question_id, answer)
    # persist if application_id provided
    if application_id:
        try:
            from backend.round2.service import persist_round2_subresult

            persist_round2_subresult(application_id, "aptitude", res.get("score", 0), artifacts={"question_id": question_id, "correct": res.get("correct")})
        except Exception:
            pass
    return res


@router.get("/dsa/{role}")
def dsa_questions(role: str):
    return sample_dsa_questions(role)


@router.post("/dsa/submit")
def submit_dsa(question_id: int = Form(...), solved: bool = Form(False), application_id: int | None = Form(None)):
    score = 100 if solved else 0
    if application_id:
        try:
            r2service.persist_round2_subresult(application_id, "dsa", score, artifacts={"question_id": question_id, "solved": solved})
        except Exception:
            pass
    return {"score": score}


@router.post("/run-code")
def run_code(language: str = Form(...), code: str = Form(...), application_id: int | None = Form(None)):
    from backend.round2.code_runner import run_code as runner

    rc, out, err = runner(language, code, timeout=10)
    # persist technical subresult if application provided
    if application_id:
        scr = 100 if rc == 0 else 20
        try:
            r2service.persist_round2_subresult(application_id, "technical", scr, artifacts={"rc": rc, "out": out, "err": err})
        except Exception:
            pass
    return {"returncode": rc, "stdout": out, "stderr": err}


@router.post("/final-score")
def final_score(scores: dict, hints_used: int = 0, application_id: int | None = None):
    agg = r2service.finalize_round2(application_id if application_id else 0, scores, hints_used)
    return agg
