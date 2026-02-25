import os
import json
import asyncio
import base64

from google import genai
from dotenv import load_dotenv

load_dotenv(override=True)
client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))

MODEL = "gemini-2.5-flash"

# Questions that have room_type="" in the JSON but are clearly room-specific.
# Key = question ID, Value = list of room names where it applies.
ROOM_SPECIFIC_QUESTION_IDS = {
    "171": ["Bedroom"],
    "172": ["Bedroom"],
    "173": ["Bedroom"],
    "174": ["Bedroom"],
    "3":   ["Basement"],
    "5":   ["SUN RM", "PORCH", "POOL RM", "DECK", "PATIO", "LANAI"],
}


def _build_prompt(questions: list[dict]) -> str:
    lines = [
        "You are inspecting a house image. Answer ONLY based on what you can see.",
        "Return answers as a JSON object where key = question id, value = one of the allowed options.",
        "If unsure, pick the closest matching option.",
        "",
        "Questions:",
    ]
    for q in questions:
        options_str = " | ".join(q["options"])
        lines.append(f'  ID "{q["id"]}": {q["text"]}')
        lines.append(f'  Options: [{options_str}]')
        lines.append("")
    lines.append('Respond with ONLY valid JSON: {"id1": "answer1", "id2": "answer2"}')
    return "\n".join(lines)


async def ask_questions_batch(image_bytes: bytes, questions: list[dict]) -> dict:
    if not questions:
        return {}

    prompt = _build_prompt(questions)
    image_b64 = base64.b64encode(image_bytes).decode("utf-8") #base64 encoded image.

    def _call_gemini():
        response = client.models.generate_content(
            model=MODEL,
            contents=[{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
                    {"text": prompt},
                ],
            }],
        )
        return response.text

    raw_text = await asyncio.get_event_loop().run_in_executor(None, _call_gemini)

    try:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        answers = json.loads(text.strip())
    except Exception:
        answers = {}

    return answers


def should_ask(question: dict, detected_room: str) -> bool:
    q_id = question["id"]

    # 1. Always ask room detector
    if q_id == "root__room_type":
        return True

    # 2. Manually mapped room-specific questions
    if q_id in ROOM_SPECIFIC_QUESTION_IDS:
        allowed_rooms = [r.lower() for r in ROOM_SPECIFIC_QUESTION_IDS[q_id]]
        return detected_room in allowed_rooms

    # 3. JSON-defined room_type restriction
    room_type = question.get("room_type", "").strip().lower()
    if room_type and room_type != "ROOT":
        return room_type.lower() == detected_room

    # 4. Global question
    return True


async def run_leveled_qa(image_bytes: bytes, questions_by_id: dict, levels: dict) -> tuple:
    all_answers = {}
    answered_ids = set()
    max_level = max(levels.keys()) if levels else 1

    level1_questions = levels.get(1, [])

    # --- Step 1: Ask ONLY the room detector first ---
    root_question = next((q for q in level1_questions if q["id"] == "root__room_type"), None)
    if root_question:
        root_answer = await ask_questions_batch(image_bytes, [root_question])
        all_answers.update(root_answer)
        answered_ids.add("root__room_type")

    detected_room = all_answers.get("root__room_type", "Unknown")
    # Normalize once here
    if isinstance(detected_room, str):
        detected_room = detected_room.strip().lower()
    else:
        detected_room = "unknown"
    print(f"[INFO] Detected room: {detected_room}")

    # --- Step 2: Ask remaining Level 1 questions, filtered by room ---
    remaining_level1 = [
        q for q in level1_questions
        if q["id"] not in answered_ids and should_ask(q, detected_room)
    ]
    if remaining_level1:
        batch_answers = await ask_questions_batch(image_bytes, remaining_level1)
        all_answers.update(batch_answers)
        answered_ids.update(batch_answers.keys())

    # --- Step 3: Levels 2 and beyond ---
    for level in range(2, max_level + 1):
        level_questions = levels.get(level, [])

        activated = []
        for q in level_questions:
            if q["id"] in answered_ids:
                continue

            if not should_ask(q, detected_room):
                continue

            deps = q.get("depends_on", [])
            if not deps:
                activated.append(q)
                continue

            all_satisfied = all(
                all_answers.get(dep["question_id"]) in dep.get("equals_any", [])
                for dep in deps
            )
            if all_satisfied:
                activated.append(q)

        if activated:
            batch_answers = await ask_questions_batch(image_bytes, activated)
            all_answers.update(batch_answers)
            answered_ids.update(q["id"] for q in activated)

    return all_answers, detected_room