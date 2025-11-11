import functions
import requests
from datetime import datetime
import time
from pymongo import MongoClient

current_dateTime = datetime.now()

#Cette fonction récupère un flux bluesky, liste ses posts et les enregistre dans mongodb
def fetch_and_store_items(endpoint: str, params: dict, source_name: str):
    token = functions.load_token(functions.LOGIN, functions.PASS)
    if not token:
        raise SystemExit("Impossible d’obtenir un access token.")

    headers = {"Authorization": f"Bearer {token}"}
    total = 0
    inserted = 0
    updated = 0
    cursor = None

    while True:
        if cursor:
            params["cursor"] = cursor

        r = requests.get(f"{functions.API_BASE}/{endpoint}", headers=headers, params=params)
        
        # Gestion d’un token expiré (Fait par ChatGPT)
        if r.status_code == 400 and "ExpiredToken" in r.text:
            print("Token expiré, tentative de refresh...")
            token = functions.refresh_token()
            if not token:
                raise SystemExit("Échec du rafraîchissement du token.")
            headers = {"Authorization": f"Bearer {token}"}
            # On relance la requête après refresh
            r = requests.get(f"{functions.API_BASE}/{endpoint}", headers=headers, params=params)
                
        if r.status_code != 200:
            print(f"Erreur API ({endpoint}) :", r.status_code, r.text)
            break

        data = r.json()

        # Gestion flexible : certains endpoints renvoient "posts", d'autres "feed"
        items = data.get("posts") or data.get("feed") or []
        cursor = data.get("cursor")

        if not items:
            print("Aucun item trouvé ou fin de flux.")
            break

        for it in items:
            # Certains flux ont les posts directement dans items, d’autres sous 'post'
            post = it.get("post", it)
            record = post.get("record", {})
            text = record.get("text", "")
            author_info = post.get("author", {})
            cid = post.get("cid")
            uri = post.get("uri")

            doc = {
                "fetched_at": current_dateTime,
                "source": source_name,
                "post_id": uri,
                "cid": cid,
                "profile_id": author_info.get("did"),
                "profile_name": author_info.get("handle", "unknown"),
                "profile_display_name": author_info.get("displayName") or "Unknown",
                "text_raw": text,
                "engagement": {
                    "likeCount": post.get("likeCount", 0),
                    "repostCount": post.get("repostCount", 0),
                    "quoteCount": post.get("quoteCount", 0),
                    "bookmarkCount": post.get("bookmarkCount", 0),
                    "replyCount": post.get("replyCount", 0)
                },
            }

            existing = functions.COLLECTION.find_one({"post_id": uri})

            if existing:
                # Si le cid a changé → le post a été modifié
                if existing.get("cid") != cid:
                    functions.COLLECTION.update_one(
                        {"_id": existing["_id"]},
                        {"$set": doc}
                    )
                    updated += 1
                    print(f"Post mis à jour : {author_info.get('handle')} ({uri})")
                else:
                    continue
            else:
                # Nouveau post
                functions.COLLECTION.insert_one(doc)
                inserted += 1
                print(f"Nouveau post : {author_info.get('handle')} → {text[:50]!r}")

        total += len(items)
        print(f"Batch traité : {len(items)} posts | Total : {total} | Cursor: {cursor}\n")

        if not cursor:
            break

        time.sleep(0.2)

    print(f"Fin du flux {source_name} — {inserted} insérés, {updated} mis à jour, {total} lus.")

    
def get_search_post(query: str, limit = 50):
    params = {"q": query, "limit": limit}
    fetch_and_store_items('app.bsky.feed.searchPosts', params, f"search_{query.replace(' ', '_')}")

for collection, queries in functions.SEARCH_QUERIES.items():
        print(f"\n=== Traitement catégorie : {collection} ===")
        
        for q in queries:
            get_search_post(q, limit=50)