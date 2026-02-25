import json

def load_questions(json_path: str = "vision_graph_5.json"):
    """
    Load the JSON and return two things:
    1. questions_by_id  -> dict { question_id: question_dict }
    2. levels           -> dict { level_number: [question_dict, ...] }

    The JSON has two top-level question groups:
      - global_questions  → apply to every room
      - rooms             → { "Kitchen": { "1": [...], "2": [...] }, "Bathroom": ... }
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    questions_by_id = {}   # id -> question dict
    levels = {}            # level (int) -> list of question dicts

    def process_section(section: dict):
        for level_str, questions in section.items():
            level = int(level_str)
            if level not in levels:
                levels[level] = []
            for q in questions:
                questions_by_id[q["id"]] = q
                levels[level].append(q)

    # 1. Global questions (apply to all rooms)
    if "global_questions" in data:
        process_section(data["global_questions"])

    # 2. Room-specific questions (key is "rooms", not "room_specific_questions")
    if "rooms" in data:
        for room_name, room_levels in data["rooms"].items():
            process_section(room_levels)

    return questions_by_id, levels