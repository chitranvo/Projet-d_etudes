import getItems

def get_author_feed(actor: str, limit: int = 50):
    params = {"actor": actor, "limit": limit}
    getItems.fetch_and_store_items("app.bsky.feed.getAuthorFeed", params, source_name="author_feed")

def get_timeline(limit: int = 50):
    params = {"limit": limit}
    getItems.fetch_and_store_items("app.bsky.feed.getTimeline", params, source_name="timeline")
    
def get_search_post(query: str, limit = 50):
    params = {"q": query, "limit": limit}
    getItems.fetch_and_store_items('app.bsky.feed.searchPosts', params, f"search_{query.replace(' ', '_')}")
    
if __name__ == "__main__":
    if not getItems.functions.LOGIN or not getItems.functions.PASS:
        raise SystemExit("LOGIN_BLUESKY et PASS_BLUESKY non définis dans .env")
    for i, target in enumerate(getItems.functions.TARGET):
        get_author_feed(getItems.functions.TARGET[i]['handle'])
    
    get_timeline()
    
    for collection, queries in getItems.functions.SEARCH_QUERIES.items():
        print(f"\n=== Traitement catégorie : {collection} ===")
        
        for q in queries:
            get_search_post(q, limit=50)
