"""Import vlastní trasy z GPX (export z Mapy.com) -> data/route_legs.json.
Použití: python3 data/import_gpx.py [cesta.gpx]  (default data/route_user.gpx)
Pak spustit: fetch_pois, fetch_elev, process, fetch_photos, fetch_ratings, build_data."""
import xml.etree.ElementTree as ET, math, json, sys

src = sys.argv[1] if len(sys.argv) > 1 else "data/route_user.gpx"
root = ET.parse(src).getroot()
ns = {'g': root.tag.split('}')[0].strip('{')}
pts = [(float(p.get('lat')), float(p.get('lon')))
       for seg in root.findall('g:trk/g:trkseg', ns)
       for p in seg.findall('g:trkpt', ns)]

def d(a, b):
    dx = (a[1]-b[1]) * 111320 * math.cos(math.radians((a[0]+b[0])/2))
    dy = (a[0]-b[0]) * 110540
    return math.hypot(dx, dy)

L = sum(d(a, b) for a, b in zip(pts, pts[1:]))
legs = [{"from": "start", "to": "cíl", "length_m": round(L), "duration_s": int(L/1.1),
         "coords": [[lon, lat] for lat, lon in pts]}]
json.dump(legs, open("data/route_legs.json", "w"))
print(f"{src}: {L/1000:.1f} km, {len(pts)} bodů -> data/route_legs.json")
