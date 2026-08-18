import json, urllib.request, urllib.parse, time, sys

pois = json.load(open("data/pois.json"))
targets = [p for p in pois if p["cat"] in ("shelter","water","food","lodging") and p["off"] <= 1200]
print(f"{len(targets)} POIs to check", file=sys.stderr)

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "trek-planner/1.0 (petr.schonfeld@gmail.com)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)

def commons_thumb(title, width=560):
    q = urllib.parse.urlencode({"action":"query","titles":title,"prop":"imageinfo","iiprop":"url","iiurlwidth":width,"format":"json"})
    d = get("https://commons.wikimedia.org/w/api.php?" + q)
    for pg in d.get("query",{}).get("pages",{}).values():
        ii = pg.get("imageinfo",[{}])[0]
        if ii.get("thumburl"): return {"thumb": ii["thumburl"], "page": ii.get("descriptionurl","")}
    return None

photos, hits = {}, 0
for i, p in enumerate(targets):
    ph = None
    t = p["tags"]
    img = t.get("image","")
    if img.startswith("http") and any(img.lower().split("?")[0].endswith(e) for e in (".jpg",".jpeg",".png",".webp")):
        ph = {"thumb": img, "page": img}
    elif t.get("wikimedia_commons","").startswith("File:"):
        ph = commons_thumb(t["wikimedia_commons"]); time.sleep(0.1)
    if ph is None and p["cat"] in ("shelter","water"):  # geosearch only for nature POIs (pubs would match random village photos)
        q = urllib.parse.urlencode({"action":"query","list":"geosearch","gscoord":f'{p["lat"]}|{p["lon"]}',
                                    "gsradius":80,"gslimit":1,"gsnamespace":6,"format":"json"})
        try:
            d = get("https://commons.wikimedia.org/w/api.php?" + q)
            gs = d.get("query",{}).get("geosearch",[])
            if gs: ph = commons_thumb(gs[0]["title"])
        except Exception as e:
            print("geosearch err", e, file=sys.stderr)
        time.sleep(0.12)
    if ph: photos[p["id"]] = ph; hits += 1
    if (i+1) % 40 == 0: print(f"  {i+1}/{len(targets)} ({hits} photos)", file=sys.stderr)

json.dump(photos, open("data/photos.json","w"))
print(f"photos: {hits}/{len(targets)}")
