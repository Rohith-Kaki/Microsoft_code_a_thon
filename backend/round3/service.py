from backend.round3.scenario_engine import generate_scenarios, evaluate_response
from backend.database.db import get_session
from backend.database.models import RoundResult, Application


def start_scenarios(application_id: int, n: int = 3):
    session = get_session()
    app = session.query(Application).filter(Application.id == application_id).first()
    if not app:
        session.close()
        raise ValueError("application not found")
    scenarios = generate_scenarios(app.jd_text or "", n=n)
    session.close()
    return scenarios


def submit_response(application_id: int, scenario_id: int, response_text: str):
    result = evaluate_response(response_text)
    session = get_session()
    rr = RoundResult(application_id=application_id, round_name="round3", score=result.get("score"), passed=(1 if result.get("score",0)>=30 else 0), artifacts={"scenario_id": scenario_id, "eval": result})
    session.add(rr)
    session.commit()
    session.close()
    return {"score": result.get("score"), "passed": (1 if result.get("score",0)>=30 else 0), "eval": result}
