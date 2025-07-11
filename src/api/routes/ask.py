from fastapi import APIRouter, WebSocket
from src.api.schemas.ask import AskRequest, AskResponse
from src.api.dependencies.services import rag_agent, llm
from src.utils.metrics import questions_total, latency_seconds, llm_failures_total
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(req: AskRequest):
    questions_total.inc()
    start = time.time()
    try:
        result = rag_agent.answer_question(req.question)
        latency_seconds.observe(time.time() - start)
        return AskResponse(answer=result["answer"], sources=result["sources"])
    except Exception:
        llm_failures_total.inc()
        raise


@router.websocket("/ws/ask/stream")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    data = await websocket.receive_json()
    prompt = data.get("prompt", "")
    if not prompt:
        await websocket.send_json({"error": "Prompt is required"})
        await websocket.close()
        return

    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def token_callback(token: str):
        loop.call_soon_threadsafe(queue.put_nowait, token)

    def run_generate():
        try:
            llm.generate(prompt=prompt, stream_callback=token_callback)
            loop.call_soon_threadsafe(queue.put_nowait, None)
        except Exception as e:
            loop.call_soon_threadsafe(queue.put_nowait, f"[Error] {str(e)}")
            loop.call_soon_threadsafe(queue.put_nowait, None)

    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, run_generate)

    while True:
        token = await queue.get()
        if token is None:
            break
        await websocket.send_text(token)

    await websocket.close()
