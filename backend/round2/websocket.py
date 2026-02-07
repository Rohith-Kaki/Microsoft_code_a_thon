from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.round2.interviewer import SimpleInterviewer

router = APIRouter()


@router.websocket("/ws/{application_id}")
async def websocket_endpoint(websocket: WebSocket, application_id: int):
    await websocket.accept()
    interviewer = SimpleInterviewer()
    try:
        await websocket.send_text("Connected to AI interviewer. Say 'start' to begin.")
        while True:
            data = await websocket.receive_text()
            if data.lower().strip() == "hint":
                hint = interviewer.give_hint(0)
                await websocket.send_text(f"HINT: {hint}")
            elif data.lower().strip() == "start":
                await websocket.send_text(interviewer.prompt_for_dive(""))
            else:
                # generic short feedback
                await websocket.send_text(interviewer.short_feedback(True))
    except WebSocketDisconnect:
        return
