"""Logo sklepów dla kart lojalnościowych (widok Karty).

Dla każdej karty (frontend user data "karty_lojalnosciowe" wszystkich użytkowników) szuka logo:
  1. Wikidata (właściwość P154 "logo" marki, aktualna wersja) -> miniatura 400 px z Wikimedia Commons,
  2. strona sklepu (domena z karty lub z www/karty/sklepy.json) -> największa ikona (apple-touch-icon / SVG),
  3. ikona z Google (tylko jeśli >= 64 px).
Wynik zapisuje raz do /config/www/karty/logos/<klucz>.<ext>; nieudane próby ponawia po 7 dniach.
Wypisuje JSON {"count": n, "logos": {klucz: "/local/karty/logos/..."}} dla sensora command_line.
Klucz = nazwa karty bez polskich znaków, spacji i interpunkcji (np. "Circle K" -> "circlek").
"""
import glob, html.parser, json, os, re, struct, time, unicodedata, urllib.parse, urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /config
OUT = os.path.join(BASE, "www", "karty", "logos")
MISS = os.path.join(OUT, "_brak.json")
BROWSER = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36",
           "Accept-Language": "pl-PL,pl;q=0.9"}
WIKI = {"User-Agent": "HomeAssistant-KartyLojalnosciowe/1.0 (prywatny dashboard domowy)"}


def norm(s):
    s = unicodedata.normalize("NFKD", (s or "").replace("ł", "l").replace("Ł", "L").lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", s)


def get(url, headers, limit=3_000_000):
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15) as r:
        return r.geturl(), r.read(limit)


_last = [0.0]
def wiki_json(url):
    for attempt in range(3):
        wait = 1.2 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            return json.loads(get(url, WIKI)[1])
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(5 * (attempt + 1)); continue
            raise
    raise RuntimeError("Wikidata: za dużo zapytań")


def img_size(data):
    if data[:8] == b"\x89PNG\r\n\x1a\n": return struct.unpack(">II", data[16:24])[0]
    if data[:4] == b"\x00\x00\x01\x00":
        n = struct.unpack("<H", data[4:6])[0]
        return max((data[6 + 16 * i] or 256) for i in range(n)) if n else 0
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9 and data[i] == 0xFF:
            m, ln = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
            if m in (0xC0, 0xC1, 0xC2): return struct.unpack(">HH", data[i + 5:i + 9])[1]
            i += 2 + ln
    if b"<svg" in data[:3000]: return 1000
    return 0


def ext_of(data):
    return "svg" if b"<svg" in data[:3000] else "png" if data[:4] == b"\x89PNG" else "ico" if data[:4] == b"\x00\x00\x01\x00" else "jpg"


def from_wikidata(name):
    r = wiki_json("https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&language=pl&uselang=pl&type=item&limit=5&search="
                  + urllib.parse.quote(name))
    want = norm(name)
    for it in r.get("search", []):
        # tylko dokładne trafienie nazwy marki – inaczej łatwo o logo zupełnie innej firmy
        if want not in (norm(it.get("label")), norm((it.get("match") or {}).get("text"))):
            continue
        claims = wiki_json(f"https://www.wikidata.org/wiki/Special:EntityData/{it['id']}.json")["entities"][it["id"]].get("claims", {}).get("P154")
        if not claims: continue
        # aktualne logo: ranga "preferred", inaczej bez daty końca (P582), inaczej ostatnie
        cur = [c for c in claims if c.get("rank") == "preferred"] or [c for c in claims if "P582" not in c.get("qualifiers", {})] or claims[-1:]
        f = cur[-1]["mainsnak"]["datavalue"]["value"]
        info = wiki_json("https://commons.wikimedia.org/w/api.php?action=query&format=json&prop=imageinfo&iiprop=url&iiurlwidth=400&titles="
                         + urllib.parse.quote("File:" + f))
        page = next(iter(info["query"]["pages"].values()))
        url = page["imageinfo"][0].get("thumburl") or page["imageinfo"][0]["url"]
        time.sleep(1)
        return get(url, WIKI)[1]
    return None


class Links(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.icons = []
    def handle_starttag(self, tag, a):
        a = dict(a)
        rel = (a.get("rel") or "").lower()
        if tag == "link" and a.get("href") and ("icon" in rel or "apple-touch" in rel) and "mask-icon" not in rel:
            sz = max([int(x) for x in re.findall(r"(\d+)x\d+", a.get("sizes") or "")] or [0])
            self.icons.append((sz or (180 if "apple" in rel else 32), a["href"]))


def from_site(domain):
    domain = re.sub(r"^https?://", "", domain.strip().lower()).split("/")[0]
    cands, base = [], "https://" + domain + "/"
    try:
        base, body = get(base, BROWSER)
        p = Links(); p.feed(body.decode("utf-8", "ignore"))
        cands = [(s, urllib.parse.urljoin(base, h)) for s, h in p.icons]
    except Exception:
        pass
    cands += [(180, urllib.parse.urljoin(base, "/apple-touch-icon.png")), (0, f"https://www.google.com/s2/favicons?domain={domain}&sz=256")]
    best = None
    for _, u in sorted(cands, key=lambda c: -c[0]):
        try: data = get(u, BROWSER, 2_000_000)[1]
        except Exception: continue
        s = img_size(data)
        if s and (best is None or s > best[0]): best = (s, data)
        if best and best[0] >= 160: break
    return best[1] if best and best[0] >= 64 else None


def cards():
    shops = json.load(open(os.path.join(BASE, "www", "karty", "sklepy.json"), encoding="utf-8"))
    aliases = shops.pop("_alias", {})
    out = {}
    for path in glob.glob(os.path.join(BASE, ".storage", "frontend.user_data_*")):
        try: cs = (json.load(open(path, encoding="utf-8"))["data"].get("karty_lojalnosciowe") or {}).get("cards", [])
        except Exception: continue
        for c in cs:
            brand_name = re.split(r"\s+[-–—]\s*|\s*[-–—]\s+|\s*\(", (c.get("name") or "").strip())[0]  # "Makro – firmowa" -> "Makro"
            k = norm(brand_name)
            if k and not c.get("nologo"):
                brand = aliases.get(k, brand_name)
                out[k] = (brand, (c.get("domain") or "").strip() or shops.get(k) or shops.get(norm(brand)))
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    try: miss = json.load(open(MISS))
    except Exception: miss = {}
    have = {os.path.splitext(f)[0]: f for f in os.listdir(OUT) if not f.startswith("_")}
    res = {}
    for k, (name, domain) in cards().items():
        if k in have:
            res[k] = "/local/karty/logos/" + have[k]; continue
        if time.time() - miss.get(k, 0) < 7 * 86400:
            continue
        data = None
        try: data = from_wikidata(name)
        except Exception: pass
        if (not data or img_size(data) < 64) and domain:
            try: data = from_site(domain)
            except Exception: data = None
        if data and img_size(data) >= 64:
            fn = f"{k}.{ext_of(data)}"
            with open(os.path.join(OUT, fn), "wb") as f: f.write(data)
            res[k] = "/local/karty/logos/" + fn
            miss.pop(k, None)
        else:
            miss[k] = time.time()
    json.dump(miss, open(MISS, "w"))
    print(json.dumps({"count": len(res), "logos": res}, ensure_ascii=False))
