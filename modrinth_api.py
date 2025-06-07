import os
import json
import requests

MODRINTH_TOKEN = os.environ.get("MODRINTH_TOKEN", "mrp_0nUiSOTSQ7Xar35PfRapMOIwXH5CA4QaV3BMOSGlwmsAaxfjTgPWmyM6CQFg")
BASE_URL = "https://api.modrinth.com/v2"


class ModrinthAPI:
    def __init__(self, token: str | None = None):
        self.token = token or MODRINTH_TOKEN
        self.session = requests.Session()
        if self.token:
            self.session.headers.update({"Authorization": self.token})

    def search_mods(
        self,
        query: str,
        limit: int = 20,
        versions: list[str] | None = None,
        loaders: list[str] | None = None,
    ):
        if not query:
            return []
        url = f"{BASE_URL}/search"
        params = {"query": query, "limit": limit}
        facets = []
        if versions:
            facets.append([f"versions:{v}" for v in versions])
        if loaders:
            facets.append([f"categories:{l}" for l in loaders])
        if facets:
            params["facets"] = json.dumps(facets)
        r = self.session.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        return data.get("hits", [])
