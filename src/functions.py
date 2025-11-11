import os
import json
import requests
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

LOGIN = os.getenv("LOGIN_BLUESKY")
PASS = os.getenv("PASS_BLUESKY")
TARGET = [
    {"handle": "aoc.bsky.social", "name": "Alexandria Ocasio-Cortez"},
    {"handle": "mcuban.bsky.social", "name": "Mark Cuban"},
    {"handle": "georgetakei.bsky.social", "name": "George Takei"},
    {"handle": "markhamillofficial.bsky.social", "name": "Mark Hamill"},
    {"handle": "theonion.com", "name": "The Onion"},
    {"handle": "nytimes.com", "name": "The New York Times"},
    {"handle": "stephenking.bsky.social", "name": "Stephen King"},
    {"handle": "maddow.msnbc.com", "name": "Rachel Maddow"},
    {"handle": "meidastouch.com", "name": "MeidasTouch"},
    {"handle": "npr.org", "name": "NPR"},
    {"handle": "atrupar.com", "name": "Aaron Rupar"},
    {"handle": "bryantylercohen.bsky.social", "name": "Bryan Tyler Cohen"},
    {"handle": "hankgreen.bsky.social", "name": "Hank Green"},
    {"handle": "gtconway.bsky.social", "name": "George Conway"},
    {"handle": "washingtonpost.com", "name": "The Washington Post"},
    {"handle": "mollyjongfast.bsky.social", "name": "Molly Jong-Fast"},
    {"handle": "chrishayes.bsky.social", "name": "Chris Hayes"},
    {"handle": "ronfilipkowski.bsky.social", "name": "Ron Filipkowski"},
    {"handle": "neiltyson.bsky.social", "name": "Neil deGrasse Tyson"},
    {"handle": "ava.bsky.social", "name": "Ava DuVernay"}
]

API_BASE = "https://bsky.social/xrpc"

SEARCH_QUERIES = {
    "feed_trending": ["breaking", "urgent", "live"],
    "feed_hot_topics": ["politics", "election", "covid", "crisis"],
    "feed_discover": ["news", "world", "science", "tech"],
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

MONGODB = os.getenv("PASS_MONGODB")
DATABASE = os.getenv("DATABASE")

CLIENT = MongoClient(MONGODB)
DB = CLIENT["stagging_bluesky"]
COLLECTION = DB["raw_data"]
    
def login(identifier: str, password: str, timeout: int = 10):
    
    #Récupération de l'URL de l'API et connexion
    url = f"{API_BASE}/com.atproto.server.createSession"
    payload = {"identifier": identifier, "password": password}

    #Tout ce bloc sert à la connexion utilisateur et à la récupération des différents tokens
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

        #Si on a les token, on les écrits dans un fichier tokens.json
        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"accessJwt": access, "refreshJwt": refresh},
                f, ensure_ascii=False, indent=2
            )
        print("Connexion OK — token enregistré dans token.json")
        return access
    except Exception as e:
        print("Erreur login :", e)
        return None
 
def load_token(identifier: str = None, password: str = None):
    if not os.path.exists(TOKEN_FILE):
        print(f"Aucun token trouvé à {TOKEN_FILE}")
        if identifier and password:
            print("Tentative de connexion automatique...")
            return login(identifier, password)
        raise FileNotFoundError("token.json introuvable")

    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("accessJwt")
    except json.JSONDecodeError as e:
        print("Token corrompu :", e)
        if identifier and password:
            return login(identifier, password)



def headers(self):
    return {"Authorization": f"Bearer {self.token}"}

#Généré par Chatgpt -> Gestion de l'expiration des tokens
def refresh_token():
    """Renouvelle le token d'accès à partir du refreshJwt."""
    if not os.path.exists(TOKEN_FILE):
        print("Aucun fichier de token trouvé pour le refresh.")
        return login(LOGIN, PASS)

    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            tokens = json.load(f)
            refresh = tokens.get("refreshJwt")
            if not refresh:
                print("Aucun refresh token trouvé, reconnexion...")
                return login(LOGIN, PASS)

        url = f"{API_BASE}/com.atproto.server.refreshSession"
        headers = {"Authorization": f"Bearer {refresh}"}
        r = requests.post(url, headers=headers, timeout=10)

        if r.status_code != 200:
            print("Échec du refresh :", r.status_code, r.text)
            # Si le refresh échoue, on relogue complètement
            return login(LOGIN, PASS)

        data = r.json()
        new_access = data.get("accessJwt")
        new_refresh = data.get("refreshJwt")

        if not new_access:
            print("Pas de nouveau token reçu, reconnexion complète...")
            return login(LOGIN, PASS)

        with open(TOKEN_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"accessJwt": new_access, "refreshJwt": new_refresh},
                f, ensure_ascii=False, indent=2
            )
        print("Token rafraîchi avec succès.")
        return new_access

    except Exception as e:
        print("Erreur lors du refresh :", e)
        return login(LOGIN, PASS)
