import json, math

legs = json.load(open("data/route_legs.json"))
pois = json.load(open("data/pois.json"))
eles = json.load(open("data/elevation.json"))
photos = json.load(open("data/photos.json"))

coords = []
for l in legs: coords += l["coords"]

def m_between(a, b):
    dx = (a[0]-b[0]) * 111320 * math.cos(math.radians((a[1]+b[1])/2))
    dy = (a[1]-b[1]) * 110540
    return math.hypot(dx, dy)

cum = [0.0]
for p, q in zip(coords, coords[1:]): cum.append(cum[-1] + m_between(p, q))

samples, acc, km = [(coords[0][0], coords[0][1], 0.0)], 0.0, 0.0
for p, q in zip(coords, coords[1:]):
    d = m_between(p, q); km += d; acc += d
    if acc >= 250: samples.append((q[0], q[1], km)); acc = 0
samples.append((coords[-1][0], coords[-1][1], km))
assert len(samples) == len(eles), (len(samples), len(eles))
profile = [{"km": round(s[2]/1000,3), "ele": e["ele"], "lat": round(s[1],6), "lon": round(s[0],6)}
           for s, e in zip(samples, eles)]

BOUNDS = [0, 19.3, 45.1, 66.8, 83.0, cum[-1]/1000 + 1]
META = [
  {"n":1,"day":"Středa 19. 8.","name":"Púchov → Vršatec","color":"#e74c3c",
   "desc":"Start v poledne z nádraží v Púchově. Výstup přes Lachovec na hřeben, výhledy na Považí, závěr pod Vršateckými bradly – nejfotogeničtější skály Bílých Karpat. Večeře v Chatě Vršatec.",
   "sleep":"Přístřešky u Vršatce (km 18,8 / 19,3); uzavíratelná útulna „Domček“ už na km 16,4"},
  {"n":2,"day":"Čtvrtek 20. 8.","name":"Vršatec → útulna za Chladným vrchem","color":"#e67e22",
   "desc":"Hřebenovka po červené (Cesta hrdinov SNP / E8) kolem Vršateckých bradel, sestup do Vlárského průsmyku (železnice, hospoda, možnost doplnit zásoby v Sidonii). Odpoledne zpět na hřeben přes Chladný vrch (742 m) k útulně s ohništěm.",
   "sleep":"Útulna s ohništěm přímo na trase (km 45,1)"},
  {"n":3,"day":"Pátek 21. 8.","name":"→ Veľký Lopeník","color":"#27ae60",
   "desc":"Pastevecké hřebeny moravských kopanic. V poledne Starý Hrozenkov (obchod – doplnění zásob, hospoda), odpoledne Mikulčin vrch s restaurací a výstup na Veľký Lopeník (911 m) s rozhlednou.",
   "sleep":"Přístřešek u Veľkého Lopeníka (km 66,8), rozhledna na dohled"},
  {"n":4,"day":"Sobota 22. 8.","name":"→ přes Veľkou Javorinu","color":"#2980b9",
   "desc":"Sestup do sedla a dlouhý výstup na Veľkou Javorinu (970 m) – nejvyšší vrchol Bílých Karpat, pomník česko-slovenské vzájemnosti. Holubyho chata pod vrcholem (pozdní oběd / večeře), pak po hřebeni k přístřešku.",
   "sleep":"Přístřešek na hřebeni za Javorinou (km 83,0)"},
  {"n":5,"day":"Neděle 23. 8.","name":"Sestup na Vrbovce, žel. st.","color":"#8e44ad",
   "desc":"Pohodový poslední úsek zvlněným hřebenem kopanic, sestup k železniční stanici Vrbovce (trať Veselí n. Moravou – Myjava). Stihnout polední/odpolední vlak.",
   "sleep":"—"},
]

days = []
for i, m in enumerate(META):
    lo, hi = BOUNDS[i], BOUNDS[i+1]
    seg = [(round(c[1],6), round(c[0],6)) for c, k in zip(coords, cum) if lo*1000 - 50 <= k <= hi*1000 + 50]
    prof = [p for p in profile if lo <= p["km"] <= hi]
    up = sum(max(0, b["ele"]-a["ele"]) for a, b in zip(prof, prof[1:]))
    dn = sum(max(0, a["ele"]-b["ele"]) for a, b in zip(prof, prof[1:]))
    dist = min(hi, cum[-1]/1000) - lo
    hours = dist/3.7 + up/450
    m.update({"kmFrom": round(lo,1), "kmTo": round(min(hi, cum[-1]/1000),1), "dist": round(dist,1),
              "up": round(up), "down": round(dn), "hours": round(hours,1), "latlngs": seg})
    days.append(m)

keep = [p for p in pois if p["off"] <= 1200 and p["cat"] != "?"]
for p in keep:
    t = p.pop("tags")
    p["sub"] = t.get("shelter_type") or t.get("tourism") or t.get("natural") or t.get("man_made") or t.get("shop") or t.get("amenity") or ""
    for k in ("opening_hours","description","note","phone","website","drinking_water","fee"):
        if t.get(k): p[k] = t[k]
    ph = photos.get(p["id"])
    if ph: p["photo"] = ph["thumb"]; p["photoPage"] = ph.get("page","")

DAYEND = [
  {"day":1,"km":19.3,"name":"Nocleh 1 – přístřešek Vršatec"},
  {"day":2,"km":45.1,"name":"Nocleh 2 – útulna s ohništěm"},
  {"day":3,"km":66.8,"name":"Nocleh 3 – přístřešek pod Lopeníkem"},
  {"day":4,"km":83.0,"name":"Nocleh 4 – přístřešek za Javorinou"},
  {"day":5,"km":round(cum[-1]/1000,1),"lat":48.8244,"lon":17.5163,"name":"Cíl – Vrbovce, žel. st."},
]
for de in DAYEND:
    if "lat" not in de:
        cands = [p for p in keep if p["cat"]=="shelter" and abs(p["km"]-de["km"]) < 0.6 and p["off"] < 250]
        best = min(cands, key=lambda p: (p["off"], abs(p["km"]-de["km"])))
        de["lat"], de["lon"] = best["lat"], best["lon"]

out = {"total": round(cum[-1]/1000,1), "days": days, "pois": keep, "profile": profile, "dayEnds": DAYEND}
with open("data.js","w") as f:
    f.write("const TREK = "); json.dump(out, f, ensure_ascii=False, separators=(",",":")); f.write(";\n")
import os
print("data.js:", os.path.getsize("data.js")//1024, "KB |", len(keep), "POIs |", sum(1 for p in keep if p.get("photo")), "photos |",
      [(d['n'], d['dist'], d['up']) for d in days])
for de in DAYEND: print(de["name"], de["lat"], de["lon"])
