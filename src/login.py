# pip install requests python-dotenv

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

LOGIN = os.getenv("LOGIN_BLUESKY")
PASS = os.getenv("PASS_BLUESKY")
TARGET = os.getenv("TARGET_BSKY") or "marshal.dev"

API_BASE = "https://bsky.social/xrpc"
TOKEN_FILE = "token.json"


# ------------------- AUTH -------------------
def login(identifier: str, password: str, timeout: int = 10):
    """Crée une session BlueSky et sauvegarde les JWT"""
    url = f"{API_BASE}/com.atproto.server.createSession"
    payload = {"identifier": identifier, "password": password}
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code != 200:
            print("Erreur de login :", r.status_code, r.text)
            return None
        data = r.json()
        access = data.get("accessJwt")
        refresh = data.get("refreshJwt")
        if not access:
            print("Login échoué — aucun accessJwt reçu")
            return None

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"accessJwt": access, "refreshJwt": refresh},
                f, ensure_ascii=False, indent=2
            )
        print("✅ Connexion OK — token enregistré dans token.json")
        return access
    except Exception as e:
        print("Erreur login :", e)
        return None


def get_access_token():
    """Lit le token d'accès depuis le fichier, ou relog si absent"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            data = json.load(f)
            token = data.get("accessJwt")
            if token:
                return token
    # Si pas de token, on relog
    return login(LOGIN, PASS)


# ------------------- FETCH -------------------
def get_author_feed(actor: str, limit: int = 50):
    """Récupère tous les posts d'un utilisateur BlueSky"""
    token = get_access_token()
    if not token:
        raise SystemExit("❌ Impossible d’obtenir un access token.")

    headers = {"Authorization": f"Bearer {token}"}
    params = {"actor": actor, "limit": limit}
    total = 0
    cursor = None

    print(f"🎯 Récupération du feed de : {actor}\n")

    while True:
        if cursor:
            params["cursor"] = cursor

        r = requests.get(
            f"{API_BASE}/app.bsky.feed.getAuthorFeed",
            headers=headers,
            params=params,
        )
        if r.status_code != 200:
            print("Erreur API :", r.status_code, r.text)
            break

        data = r.json()
        items = data.get("feed", [])
        cursor = data.get("cursor")

        if not items:
            print("Aucun item trouvé ou fin de flux.")
            break

        for it in items:
            post = it["post"]
            author = post["author"]["handle"]
            text = post["record"].get("text", "")
            print(f"{author} → {text}\n" + "-" * 60)

        total += len(items)
        print(f"Posts récupérés : {total} | Cursor: {cursor}\n")

        if not cursor:
            break

        time.sleep(0.2)  # throttle léger

    print(f"✅ Total posts récupérés : {total}")


# ------------------- MAIN -------------------
if __name__ == "__main__":
    if not LOGIN or not PASS:
        raise SystemExit("⚠️ LOGIN_BLUESKY et PASS_BLUESKY non définis dans .env")
    get_author_feed(TARGET)
