import time

from fastapi import FastAPI, File, UploadFile

from services.image import validate_image
from services.load_json import load_questions
from services.gemini import run_leveled_qa

app = FastAPI(title="House Image Q&A")

# Load questions once at startup
questions_by_id, levels = load_questions("vision_graph_5.json")


@app.post("/analyze")
async def analyze_house_image(file: UploadFile = File(...)):
    start_time = time.time()

    # Read and validate image
    image_bytes = await file.read()
    await validate_image(file, image_bytes)

    # Run the leveled Q&A pipeline
    answers, detected_room = await run_leveled_qa(image_bytes, questions_by_id, levels)

    elapsed = round(time.time() - start_time, 2)

    # Build a clean, readable list of Q&A pairs
    qa_results = []
    for q_id, answer in answers.items():
        if q_id == "root__room_type":
            continue
        question = questions_by_id.get(q_id, {})
        qa_results.append({
            "question_id": q_id,
            "question": question.get("text", "Unknown question"),
            "answer": answer,
        })

    return {
        "detected_room": detected_room,
        "processing_time_seconds": elapsed,
        "results": qa_results,
    }
