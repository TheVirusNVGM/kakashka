from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Mod:
    slug: str
    title: str
    description: str
    author: str
    version: str
    url: str
    x: float = 0
    y: float = 0


@dataclass
class Category:
    name: str
    mods: List[Mod] = field(default_factory=list)
    x: float = 0
    y: float = 0
    width: float = 200
    height: float = 150

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "mods": [mod.__dict__ for mod in self.mods],
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @staticmethod
    def from_dict(data: Dict) -> "Category":
        cat = Category(
            name=data["name"],
            x=data.get("x", 0),
            y=data.get("y", 0),
            width=data.get("width", 200),
            height=data.get("height", 150),
        )
        cat.mods = [Mod(**mod) for mod in data.get("mods", [])]
        return cat
