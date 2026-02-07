from fastapi import APIRouter, UploadFile, File, Form, Depends
from backend.round1.service import handle_application

router = APIRouter(prefix="/round1", tags=["round1"])


@router.post("/apply")
async def apply_route(job_role: str = Form(...), jd_text: str = Form(...), resume: UploadFile = File(...)):
    """Endpoint to upload resume and JD text for ATS screening."""
    contents = await resume.read()
    # create an in-memory file-like
    from io import BytesIO

    f = BytesIO(contents)
    result = handle_application(f, job_role=job_role, jd_text=jd_text)
    return result
