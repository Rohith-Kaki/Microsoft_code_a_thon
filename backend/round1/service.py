from backend.round1.resume_parser import extract_text_from_file
from backend.round1.ats_evaluator import evaluate
from backend.database.db import get_session
from backend.database.models import Candidate, Application, RoundResult


def handle_application(file, job_role: str, jd_text: str, candidate_info: dict | None = None):
    # extract text
    resume_text = extract_text_from_file(file)
    # evaluate
    result = evaluate(resume_text, jd_text)
    # persist
    session = get_session()
    candidate = None
    if candidate_info:
        candidate = Candidate(name=candidate_info.get("name"), email=candidate_info.get("email"))
        session.add(candidate)
        session.flush()
    app = Application(candidate_id=(candidate.id if candidate else None), job_role=job_role, resume_text=resume_text, jd_text=jd_text)
    session.add(app)
    session.flush()
    rr = RoundResult(application_id=app.id, round_name="round1", score=result.get("score"), passed=(1 if result.get("score",0) >= 60 else 0), artifacts={"details": result})
    session.add(rr)
    session.commit()
    session.close()
    return {"application_id": app.id, "score": result.get("score"), "passed": rr.passed, "details": result}
