import os
import requests

MODRINTH_TOKEN = os.environ.get("MODRINTH_TOKEN", "mrp_0nUiSOTSQ7Xar35PfRapMOIwXH5CA4QaV3BMOSGlwmsAaxfjTgPWmyM6CQFg")
BASE_URL = "https://api.modrinth.com/v2"


class ModrinthAPI:
    def __init__(self, token: str | None = None):
        self.token = token or MODRINTH_TOKEN
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": self.token})

    def search_mods(self, query: str, limit: int = 20):
        if not query:
            return []
        url = f"{BASE_URL}/search"
        params = {"query": query, "limit": limit}
        r = self.session.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("hits", [])
