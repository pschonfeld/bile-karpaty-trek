# Přechod Bílých Karpat · Púchov → Myjava žel. st.

Interaktivní mapa přechodu po hřebenovce Bílých Karpat, st 19. 8. – ne 23. 8. 2026.
Celkem **95,6 km**, ↑3651 m / ↓3556 m.

Trasa vychází z plánu na Mapy.com (https://mapy.com/s/jogojevesa): Púchov žst →
Chmeľová → Vršatské Podhradie → (červená hřebenovka přes Vlárský průsmyk, Mikulčin
vrch, Veľký Lopeník a Veľkou Javorinu) → Myjava žel. st. Geometrie je generovaná
routingem Mapy.cz (profil `foot_hiking`) přes tyto body — drží se značených tras.

## Spuštění
Statická aplikace:
```
python3 -m http.server 8741 --directory .
```
a otevřít http://localhost:8741. Nasazeno na GitHub Pages (push do `main`).

## Data a limity
- **Trasa**: Mapy.cz routing API přes body plánu (viz `data/fetch_route.py`).
- **Body zájmu**: OpenStreetMap (Overpass), koridor ±1,2 km — hospody, obchody,
  voda, přístřešky, útulny, ubytování. Pitnost pramenů a stav přístřešků neověřeny.
- **Hodnocení a otvíračky**: neoficiální endpointy mapy.com (viz
  `data/ratings_report.md`) — mohou se kdykoli rozbít, aplikace na nich neběží.
- **Fotky**: OSM tagy, Wikimedia Commons a Mapy.com (73 bodů s fotkou).
- **API klíč Mapy.cz** je v `index.html` (`MAPY_KEY`), omezený na doménu.
- Pipeline v `data/`: `fetch_route` (nebo `import_gpx` pro vlastní GPX) →
  `fetch_pois` → `fetch_elev` → `process` → `fetch_photos` → `fetch_ratings` →
  `build_data`.

## Než vyrazíte
- Stáhnout **GPX** tlačítkem v aplikaci (volitelně i s viditelnými body zájmu).
- V mobilní aplikaci Mapy.cz **offline mapu** Bílých Karpat — na hřebeni je slabý signál.
