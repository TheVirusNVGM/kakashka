import json
from typing import List
from models import Category


def save_schema(categories: List[Category], path: str):
    data = [cat.to_dict() for cat in categories]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_schema(path: str) -> List[Category]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [Category.from_dict(cat) for cat in data]
