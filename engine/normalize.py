def normalize_props(raw, event, sport):
    out=[]
    for book in raw.get("bookmakers",[]):
        for m in book.get("markets",[]):
            for o in m.get("outcomes",[]):
                out.append({
                    "prop_id": f"{event['id']}_{o.get('name')}",
                    "event_id": event["id"],
                    "sport": sport,
                    "player": o.get("name"),
                    "market": m.get("key"),
                    "line": o.get("point"),
                    "odds": o.get("price")
                })
    return out