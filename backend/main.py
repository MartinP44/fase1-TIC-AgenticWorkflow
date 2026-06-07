"""
FastAPI main application — CTF Challenge Reviewer Backend.
Provides file upload + SSE streaming of agent steps.
"""
import asyncio
import json
import uuid
import os
from typing import AsyncGenerator

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

from agents.graph import ctf_graph
from agents.state import CTFReviewState

app = FastAPI(
    title="CTF Challenge Reviewer",
    description="Multi-agent system that validates CTF challenge templates",
    version="1.0.0",
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job store (for production use Redis)
jobs: dict[str, dict] = {}


@app.get("/health")
async def health():
    return {"status": "ok", "model": os.getenv("OLLAMA_MODEL", "llama3")}


@app.post("/review/upload")
async def upload_challenge(file: UploadFile = File(...)):
    """
    Upload a CTF challenge file.
    Returns a job_id to poll for SSE stream.
    """
    content = await file.read()

    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File too large (max {MAX_FILE_SIZE_MB}MB)")

    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "filename": file.filename,
        "raw_bytes": content,
        "status": "pending",
    }

    return {"job_id": job_id, "filename": file.filename}


@app.get("/review/stream/{job_id}")
async def stream_review(job_id: str):
    """
    SSE endpoint — streams agent steps in real-time.
    Connect immediately after /upload.
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    async def event_generator() -> AsyncGenerator[str, None]:
        # Send initial "started" event
        yield _sse_event("pipeline_start", {
            "job_id": job_id,
            "filename": job["filename"],
            "message": "Pipeline iniciado"
        })

        await asyncio.sleep(0.1)

        try:
            # Build initial state
            initial_state = CTFReviewState(
                filename=job["filename"],
                file_content="",
                _raw_bytes=job["raw_bytes"],
                explorer_context=None,
                challenge_type=None,
                classification_confidence=None,
                classification_reason=None,
                parsed_template=None,
                findings=[],
                score=None,
                verdict=None,
                steps=[],
                error=None,
                # Nuevos campos del rediseño agéntico
                format_detected=None,
                domain_detected=None,
                template_rules=None,
                compiled_model=None,
                structural_errors=[],
                security_violations=[],
                warnings=[],
                semantic_report=None,
                agent_logs=[],
                iteration=0,
                parsed_metadata=None,
            )

            # Run graph — stream step by step
            seen_steps = 0

            # Run the graph in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            final_state = await loop.run_in_executor(
                None,
                lambda: ctf_graph.invoke(initial_state)
            )

            # Stream each step as it appears in final state
            # (LangGraph doesn't natively stream state updates in sync mode,
            #  so we re-emit steps from the final state with simulated delays)
            steps = final_state.get("steps", [])
            for step in steps:
                yield _sse_event("agent_step", step)
                await asyncio.sleep(0.3)  # visual delay for UX

            # Final verdict event
            yield _sse_event("verdict", {
                "verdict": final_state.get("verdict", "invalid"),
                "score": final_state.get("score", 0),
                "type": final_state.get("challenge_type", "unknown"),
                "findings": final_state.get("findings", []),
                "classification_reason": final_state.get("classification_reason", ""),
            })

            yield _sse_event("done", {"message": "Pipeline completado"})

        except Exception as e:
            yield _sse_event("error", {"message": str(e)})

        finally:
            # Cleanup job
            if job_id in jobs:
                del jobs[job_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
