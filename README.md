# Přechod Bílých Karpat · Púchov → Myjava žel. st.

Interaktivní plánovač 4,5denního přechodu po červené hřebenovce (Cesta hrdinov SNP / E8),
st 19. 8. – ne 23. 8. 2026. Celkem **94,2 km**, ↑3584 m / ↓3396 m. Trasa: vlastní plán z Mapy.com
(https://mapy.com/s/jogojevesa, GPX v `data/route_user.gpx`).

## Spuštění
Aplikace je statická – stačí naservírovat adresář:
```
python3 -m http.server 8741 --directory .
```
a otevřít http://localhost:8741. (Otevření `index.html` přímo souborem funguje také,
jen některé prohlížeče blokují lokální `data.js` – server je spolehlivější.)

## Etapy
| Den | Úsek | km | ↑ / ↓ | Nocleh |
|---|---|---|---|---|
| St 19. 8. | Púchov žst → hřeben pod Vršatcem | 13,4 | +655/−317 | bouda na hřebeni (km 13,4), záloha útulna „Domček“ (km 16,4) |
| Čt 20. 8. | → útulna za Chladným vrchem (bradlá, Chmeľová, Vlárský průsmyk) | 30,4 | +1162/−1102 | útulna s ohništěm přímo na trase (km 43,8) |
| Pá 21. 8. | → Veľký Lopeník (Starý Hrozenkov: obchod; Mikulčin vrch: restaurace) | 21,3 | +845/−562 | přístřešek pod rozhlednou (km 65,1) |
| So 22. 8. | → přes Veľkou Javorinu (Holubyho chata) | 19,7 | +855/−1122 | přístřešek přímo na trase (km 84,8) |
| Ne 23. 8. | → Myjava, žel. st. | 9,4 | +67/−293 | krátký dojezd na vlak |

## Data a limity
- **Trasa**: vlastní GPX z plánovače Mapy.com (`data/import_gpx.py` ji převádí do pipeline) – v terénu se držte
  červené značky, routing se od ní může místy drobně lišit.
- **POI**: OpenStreetMap (Overpass), koridor ±1,2 km. Stav přístřešků a pitnost pramenů
  neověřena – berte jako pravděpodobná, ne garantovaná místa.
- **API klíč Mapy.cz** je v `index.html` (`MAPY_KEY`) – klientský klíč, limit 250k dlaždic/měsíc.
- **Fotky**: OSM tag `image`/`wikimedia_commons` + Wikimedia Commons geosearch + fotky z Mapy.com (celkem 73 bodů s fotkou).
- **Hodnocení hospod**: veřejné API Mapy.cz hodnocení neposkytuje – v detailu bodu je odkaz
  na Mapy.com, kde je hodnocení i fotky.
- `data/` obsahuje stahovací a build skripty (`fetch_route.py`, `fetch_pois.py`,
  `fetch_elev.py`, `fetch_photos.py`, `process.py`, `build_data.py`) – po úpravě trasy spusťte v tomto pořadí.

## Než vyrazíte
- Exportujte **GPX** tlačítkem v aplikaci a nahrajte do mobilu/hodinek.
- V mobilní aplikaci Mapy.cz si stáhněte **offline mapu** Bílých Karpat – na hřebeni je slabý signál.
- Ověřte jízdní řád vlaku z Vrbovců na nedělní odpoledne.
