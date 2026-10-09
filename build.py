#!/usr/bin/env python3
"""Bouwt de statische Baitan-site naar ./dist.

Inhoud komt uit data/site.json en data/treatments.json (beheerd via Pages CMS).
Vormgeving: static/styles.css, interactie: static/app.js.
Gebruik:  python3 build.py
"""
import datetime
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "dist"
STATIC = ROOT / "static"

# ---------------------------------------------------------------- data (Pages CMS)
_site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
_treat = json.loads((ROOT / "data" / "treatments.json").read_text(encoding="utf-8"))

DOMAIN = (_site.get("seo", {}).get("canonical") or "https://baitanmassage.nl").rstrip("/")
_rating = _site.get("reviews", {}).get("rating", 4.9)
_wa = _site.get("whatsappUrl") or "https://wa.me/" + _site["phoneHref"].lstrip("+")
_wa_msg = _site.get("whatsappMessage") or "Hallo Baitan, ik heb een vraag over een massage."
_postal, _, _city = _site["postalCity"].partition(" ")
_postal2, _, _city2 = _city.partition(" ")
SITE = {
    "name": _site["businessName"],
    "tagline": _site.get("tagline", ""),
    "phone_display": _site["phoneDisplay"],
    "phone_href": _site["phoneHref"],
    "email": _site["email"],
    "street": _site["addressLine1"],
    "postal": f"{_postal} {_postal2}",
    "city": _city2,
    "region": "Zuid-Holland",
    "kvk": _site.get("kvk", ""),
    "btw": _site.get("btw", ""),
    "booking_url": _site.get("booking", {}).get("salonizedBookingUrl") or "https://baitan-thai-massage.salonized.com/services",
    "whatsapp_url": _wa,
    "whatsapp_gift_url": _wa + "?text=" + "Hallo%20Baitan%2C%20ik%20wil%20graag%20informatie%20over%20een%20cadeaubon.",
    "whatsapp_question_url": _wa + "?text=" + __import__("urllib.parse").parse.quote(_wa_msg),
    "route_url": _site.get("contact", {}).get("routeUrl", ""),
    "maps_url": _site.get("reviews", {}).get("url", ""),
    "map_embed_url": _site.get("contact", {}).get("mapEmbedUrl", ""),
    "review_write_url": _site.get("reviews", {}).get("writeUrl", ""),
    "rating": f"{float(_rating):.1f}".replace(".", ","),
    "review_count": int(_site.get("reviews", {}).get("count", 0)),
    "review_as_of": _site.get("reviews", {}).get("asOf", ""),
    "google_verification": _site.get("seo", {}).get("googleSiteVerification", ""),
}
_op = _site.get("opening", {})
HOURS = [
    {"label": _op.get("weekdayLabel", "Maandag – vrijdag").replace(" — ", " – "), "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"], "opens": _op.get("weekdayOpen", "10:00"), "closes": _op.get("weekdayClose", "21:00")},
    {"label": _op.get("weekendLabel", "Zaterdag – zondag").replace(" — ", " – "), "days": ["Saturday", "Sunday"], "opens": _op.get("weekendOpen", "11:00"), "closes": _op.get("weekendClose", "20:00")},
]
FACILITIES = list(_site.get("about", {}).get("facts", []))
DURATIONS = [60, 90, 120]
TREATMENTS = []
for _t in _treat:
    if not _t.get("active", True):
        continue
    _d = sorted(_t.get("durations", []), key=lambda d: d["minutes"])
    _is_duo = _t["id"] == "duo"
    TREATMENTS.append({
        "id": _t["id"],
        "name": _t["name"],
        "slug": _t["slug"],
        "page": _t.get("showPage", True),
        "short": _t.get("description", ""),
        "image": Path(_t.get("image", "/assets/images/thaise-massage-capelle-aan-den-ijssel.webp")).stem,
        "alt": _t.get("imageAlt", _t["name"]),
        "durations": [d["minutes"] for d in _d],
        "solo": None if _is_duo else [d["price"] for d in _d],
        "duo": [d["price"] for d in _d] if _is_duo else [d.get("duoPrice") for d in _d],
        "seo_title": _t.get("seoTitle") or f'{_t["name"]} Capelle aan den IJssel | Baitan',
        "seo_description": _t.get("seoDescription") or _t.get("description", ""),
        "h1": _t.get("h1") or f'{_t["name"]} in Capelle aan den IJssel',
        "lead": _t.get("lead") or _t.get("description", ""),
        "body": [p.strip() for p in (_t.get("detailText") or "").split("\n\n") if p.strip()],
        "steps": [(s.get("title", ""), s.get("text", "")) for s in _t.get("steps", [])],
    })
FAQ = [(f["question"], f["answer"]) for f in _site.get("faq", [])]
HERO = _site.get("hero", {})
ABOUT = _site.get("about", {})
GIFT = _site.get("giftCard", {})
LOYALTY = _site.get("loyalty", {})
SEO = _site.get("seo", {})

# Locatie volgens PDOK/Kadaster (Hollandsch Diep 71, Diepenbuurt, wijk Oostgaarde Zuid)
GEO = (51.9365043, 4.6012847)
NEIGHBOURHOOD = "Oostgaarde"
NEARBY = ["Rotterdam", "Krimpen aan den IJssel", "Nieuwerkerk aan den IJssel", "Ouderkerk aan den IJssel"]


def _euro_list(prices):
    vals = [f"€{p}" for p in prices]
    return ", ".join(vals[:-1]) + " en " + vals[-1] if len(vals) > 1 else vals[0]


def lname(name):
    """Naam midden in een zin: 'Sportmassage' -> 'sportmassage', 'Thaise massage' blijft."""
    return name if name.split()[0] in ("Thaise",) else name[0].lower() + name[1:]


def price_faq(t):
    """Vraag + antwoord over de prijs van één behandeling, altijd gelijk aan de data."""
    if t["id"] == "duo":
        lowest = min(x["duo"][0] for x in TREATMENTS if x["duo"] and x["duo"][0])
        return (f"Wat kost een duo-massage in {SITE['city']}?",
                f"Een duo-massage bij Baitan is voor twee personen samen en begint bij €{lowest} voor 60 minuten. De precieze prijs hangt af van de behandeling die jullie kiezen; je ziet alle duo-prijzen in de tabel op deze pagina.")
    durs = _euro_list(DURATIONS).replace("€", "") + " minuten"
    ans = f"Een {lname(t['name'])} bij Baitan kost {_euro_list(t['solo'])} voor respectievelijk {durs}."
    if t["duo"] and all(t["duo"]):
        ans += f" Samen als duo-massage betaal je {_euro_list(t['duo'])} voor twee personen."
    return (f"Wat kost een {lname(t['name'])} in {SITE['city']}?", ans)


# Massagekeuze. Elke vraag meet één ding: voor wie, doel, druk, extra's, duur.
# "w" = punten per behandeling, "why" = reden die in het advies verschijnt.
QUIZ = [
    {"key": "mode", "q": {"self": "Voor wie is de massage?"}, "options": [
        {"label": "Voor mezelf", "mode": "self"},
        {"label": "Voor ons samen (duo)", "mode": "duo"},
        {"label": "Als cadeau voor iemand", "mode": "gift"},
    ]},
    {"key": "goal", "q": {"self": "Wat wil je vooral bereiken?", "duo": "Wat willen jullie vooral bereiken?", "gift": "Wat gun je de ontvanger vooral?"}, "options": [
        {"label": "Helemaal tot rust komen", "w": {"aroma": 3, "hotstone": 2, "thai": 1, "scrub": 1}, "why": "Tot rust komen staat voorop"},
        {"label": "Soepeler en minder stijf worden", "w": {"thai": 3, "hotstone": 2, "sport": 1}, "why": "Soepeler en minder stijf worden"},
        {"label": "Belaste spieren losmaken (sport, werk of lang zitten)", "w": {"sport": 3, "hotstone": 1, "thai": 1}, "why": "Aandacht voor belaste spieren"},
        {"label": "Ook de huid verzorgen", "w": {"scrub": 6, "aroma": 1}, "why": "Ook verzorging voor de huid"},
    ]},
    {"key": "pressure", "q": {"self": "Hoe stevig mag de massage zijn?", "duo": "Hoe stevig mag de massage zijn?", "gift": "Hoe stevig zou de ontvanger het willen?"}, "options": [
        {"label": "Zacht en rustig", "w": {"aroma": 2, "scrub": 2}, "why": "Zachte, rustige druk"},
        {"label": "Gemiddeld", "w": {"thai": 2, "aroma": 1, "hotstone": 1}, "why": "Gemiddelde druk"},
        {"label": "Stevig", "w": {"sport": 3, "hotstone": 2, "thai": 1}, "why": "Stevige druk"},
        {"label": "Weet ik nog niet", "w": {}},
    ]},
    {"key": "extra", "q": {"self": "Wat maakt het voor jou extra fijn?", "duo": "Wat maakt het voor jullie extra fijn?", "gift": "Wat zou de ontvanger extra fijn vinden?"}, "options": [
        {"label": "Warmte", "w": {"hotstone": 4}, "why": "Warmte als extra"},
        {"label": "Een geur naar keuze", "w": {"aroma": 4}, "why": "Een geur naar keuze"},
        {"label": "Rustige rekbewegingen", "w": {"thai": 4, "aroma": 1, "hotstone": 1}, "why": "Rustige rekbewegingen"},
        {"label": "Geen voorkeur", "w": {}},
    ]},
    {"key": "duration", "q": {"self": "Hoeveel tijd wil je nemen?", "duo": "Hoeveel tijd willen jullie nemen?", "gift": "Hoe lang mag de massage duren?"}, "options": [
        {"label": "60 minuten", "dur": 60},
        {"label": "90 minuten", "dur": 90},
        {"label": "120 minuten", "dur": 120},
        {"label": "Weet ik nog niet", "dur": None},
    ]},
]
# Volgorde bij gelijke stand (na het doel van vraag 2)
QUIZ_ORDER = ["thai", "aroma", "hotstone", "sport", "scrub"]


TODAY = datetime.date.today().isoformat()
def fhash(path):
    """Korte inhoudshash: verandert alleen als het bestand verandert (voor cache-busting)."""
    import hashlib
    return hashlib.sha1(Path(path).read_bytes()).hexdigest()[:10]


# styles.css, app.js en assets/images/r/ worden een jaar 'immutable' gecachet (vercel.json).
# Daarom hangt de ?v= af van de inhoud, niet van de datum: elke wijziging krijgt een nieuwe URL.
CSS_V = fhash(ROOT / "static" / "styles.css")
JS_V = fhash(ROOT / "static" / "app.js")

E = html.escape
BIZ_ID = f"{DOMAIN}/#business"
BY_ID = {t["id"]: t for t in TREATMENTS}
PAGES = [t for t in TREATMENTS if t["page"]]


def _read_size(path):
    """Breedte/hoogte uit WebP, PNG of JPEG lezen zonder extra libraries."""
    b = path.read_bytes()
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        chunk = b[12:16]
        if chunk == b"VP8 ":
            return int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF
        if chunk == b"VP8L":
            v = int.from_bytes(b[21:25], "little")
            return (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
        if chunk == b"VP8X":
            return int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    if b[:2] == b"\xff\xd8":
        i = 2
        while i < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m = b[i + 1]
            if m in (0xC0, 0xC1, 0xC2):
                return int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big")
            i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    return 1200, 800


_SIZE_CACHE = {}


def img_size(name):
    if name not in _SIZE_CACHE:
        p = ROOT / "assets" / "images" / f"{name}.webp"
        _SIZE_CACHE[name] = _read_size(p) if p.exists() else (1200, 800)
    return _SIZE_CACHE[name]


def euro(n):
    return f"€{n}"


def ext(url):
    """Attributen voor een externe link."""
    return f'href="{E(url)}" target="_blank" rel="noopener"'


# ---------------------------------------------------------------- icons
ICONS = {
    "arrow": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "phone": '<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/>',
    "pin": '<path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 7 9 6 9-6"/>',
    "car": '<path d="M5 17h14M6 17v2M18 17v2M4 13l2-5h12l2 5v4H4z"/><circle cx="8" cy="14.5" r=".6"/><circle cx="16" cy="14.5" r=".6"/>',
    "card": '<rect x="3" y="6" width="18" height="13" rx="2"/><path d="M3 10h18M7 15h4"/>',
    "drop": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z"/>',
    "shield": '<path d="M12 3 5 6v5c0 4.5 3 8.3 7 10 4-1.7 7-5.5 7-10V6z"/><path d="m9 12 2 2 4-4"/>',
    "gift": '<rect x="4" y="9" width="16" height="11" rx="1"/><path d="M3 9h18M12 9v11M12 9c-1.5-3-5-3.5-5-1s5 1 5 1zM12 9c1.5-3 5-3.5 5-1s-5 1-5 1z"/>',
    "stamp": '<rect x="4" y="5" width="16" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><circle cx="15" cy="10" r="1.6"/><circle cx="9" cy="15" r="1.6"/><circle cx="15" cy="15" r="1.6"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
}
WHATSAPP = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true" fill="currentColor"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.2-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.9 11.9 0 0 0 4.6 4c1.7.7 2.4.8 3.2.7.5-.1 1.5-.6 1.8-1.2s.2-1.1.1-1.2-.2-.2-.5-.3z"/></svg>'
STAR = '<svg class="star" viewBox="0 0 24 24" aria-hidden="true"><path d="m12 2.8 2.8 5.8 6.3.9-4.6 4.4 1.1 6.3L12 17.3l-5.6 2.9 1.1-6.3L2.9 9.5l6.3-.9z"/></svg>'


def icon(name):
    return f'<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{ICONS[name]}</svg>'


def stars():
    return f'<span class="stars" aria-hidden="true">{STAR * 5}</span>'


# ---------------------------------------------------------------- shared parts
def preload_tags(name, sizes):
    """Preload van de hero; met mobiele uitsnede krijgt elk schermtype zijn eigen bestand."""
    if not name or not variants(name):
        return ""
    mob = f"{name}-mobiel"
    if variants(mob):
        return (f'<link rel="preload" as="image" type="image/avif" media="{MOBILE_MQ}" imagesrcset="{srcset(mob, "avif")}" imagesizes="100vw" fetchpriority="high">\n'
                f'<link rel="preload" as="image" type="image/avif" media="not all and {MOBILE_MQ}" imagesrcset="{srcset(name, "avif")}" imagesizes="{sizes}" fetchpriority="high">')
    return f'<link rel="preload" as="image" type="image/avif" imagesrcset="{srcset(name, "avif")}" imagesizes="{sizes}" fetchpriority="high">'


def head(title, description, path, og_image="og-image.jpg", schema=None, robots="index,follow,max-image-preview:large", preload_img=None, preload_sizes="100vw"):
    canonical = DOMAIN + path
    # Eigen deelafbeelding per pagina als er een passende foto is
    if og_image == "og-image.jpg" and path != "/" and preload_img and (ROOT / "static" / "og" / f"{preload_img}.jpg").exists():
        og_image = f"og/{preload_img}.jpg"
    ld = ""
    if schema:
        ld = f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": schema}, ensure_ascii=False, separators=(",", ":"))}</script>'
    return f"""<!doctype html>
<html lang="nl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(description)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<meta name="theme-color" content="#2f3829">
<meta property="og:type" content="website">
<meta property="og:locale" content="nl_NL">
<meta property="og:site_name" content="{SITE['name']}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{DOMAIN}/{og_image}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{E(title.split(' | ')[0])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" hreflang="nl-NL" href="{canonical}">
{f'<meta name="google-site-verification" content="{E(SITE["google_verification"])}">' if SITE["google_verification"] else ""}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
{preload_tags(preload_img, preload_sizes)}
<link rel="preload" href="/fonts/newsreader.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/figtree.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/styles.css?v={CSS_V}">
{ld}
</head>"""


NAV = [("/massages", "Behandelingen"), ("/prijzen", "Prijzen"), ("/cadeaubon", "Cadeaubon"), ("/massagegids", "Massagegids"), ("/over-baitan", "Over Baitan"), ("/contact", "Contact")]


def header(current=""):
    cur = ' aria-current="page"'
    links = "".join(
        f'<li><a class="nav-link" href="{href}"{cur if href == current else ""}>{label}</a></li>' for href, label in NAV
    )
    return f"""<a class="skip-link" href="#main">Naar de inhoud</a>
<header class="site-header" data-header>
  <div class="wrap header-inner">
    <a class="brand" href="/" aria-label="Baitan Thai Massage, naar de homepage">
      <img class="brand-emblem" src="/logo/baitan-emblem-96.webp" srcset="/logo/baitan-emblem-48.webp 1x, /logo/baitan-emblem-96.webp 2x, /logo/baitan-emblem-144.webp 3x" width="40" height="44" alt="">
      <img class="brand-wordmark" src="/logo/baitan-woordmerk-80.webp" srcset="/logo/baitan-woordmerk-40.webp 1x, /logo/baitan-woordmerk-80.webp 2x, /logo/baitan-woordmerk-120.webp 3x" width="79" height="28" alt="">
    </a>
    <nav class="site-nav" aria-label="Hoofdmenu">
      <ul class="nav-list" id="nav-list">{links}<li class="nav-extra">
        <a class="btn btn-primary btn-block" {ext(SITE['booking_url'])}>Afspraak maken {icon('arrow')}</a>
        <div class="nav-extra-row"><a class="btn btn-outline" href="tel:{SITE['phone_href']}">{icon('phone')} Bellen</a><a class="btn btn-outline" {ext(SITE['whatsapp_question_url'])}>{WHATSAPP} WhatsApp</a></div>
        <p class="nav-extra-status" data-open-status data-week="{week_hours_json()}">{hours_short()}</p>
      </li></ul>
    </nav>
    <div class="header-actions">
      <a class="header-phone" href="tel:{SITE['phone_href']}">{icon('phone')}<span>{SITE['phone_display']}</span></a>
      <a class="btn btn-primary btn-sm" {ext(SITE['booking_url'])}>Afspraak maken</a>
      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="nav-list" data-menu-toggle><span class="sr-only">Menu</span><span class="menu-bars" aria-hidden="true"></span></button>
    </div>
  </div>
</header>"""


def footer():
    hours = "".join(f"<li><span>{h['label']}</span><span>{h['opens']} – {h['closes']}</span></li>" for h in HOURS)
    treat = "".join(f'<li><a href="/{t["slug"]}">{t["name"]}</a></li>' for t in PAGES)
    return f"""<footer class="site-footer">
  <div class="wrap">
    <div class="footer-top">
      <div class="footer-brand">
        <a class="footer-logo" href="/" aria-label="Baitan Thai Massage, naar de homepage"><img src="/logo/baitan-logo-180.webp" srcset="/logo/baitan-logo-180.webp 1x, /logo/baitan-logo-360.webp 2x, /logo/baitan-logo-540.webp 3x" width="132" height="180" alt="Baitan Thai Massage logo" loading="lazy" decoding="async"></a>
        <p>{E(SITE['tagline'])}</p>
        <a class="btn btn-light btn-sm" {ext(SITE['booking_url'])}>Afspraak maken</a>
      </div>
      <details class="footer-group" open>
        <summary class="footer-title"><h2>Behandelingen</h2></summary>
        <ul class="footer-list">{treat}<li><a href="/prijzen">Alle prijzen</a></li></ul>
      </details>
      <details class="footer-group" open>
        <summary class="footer-title"><h2>Informatie</h2></summary>
        <ul class="footer-list">
          <li><a href="/over-baitan">Over Baitan</a></li>
          <li><a href="/cadeaubon">Cadeaubon &amp; spaarkaart</a></li>
          <li><a href="/veelgestelde-vragen">Veelgestelde vragen</a></li>
          <li><a href="/massagegids">Massagegids</a></li>
          <li><a href="/massage-voor-stellen">Massage voor stellen</a></li>
          <li><a href="/massage-na-het-sporten">Massage na het sporten</a></li>
          <li><a href="/ontspanningsmassage-capelle">Ontspanningsmassage</a></li>
        </ul>
      </details>
      <div>
        <h2 class="footer-title">Contact</h2>
        <address class="footer-list">
          <span>{SITE['street']}</span><span class="nowrap">{SITE['postal']} {SITE['city']}</span>
          <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a>
          <a href="mailto:{SITE['email']}">{SITE['email']}</a>
          <a {ext(SITE['whatsapp_question_url'])}>WhatsApp</a>
        </address>
      </div>
      <div>
        <h2 class="footer-title">Openingstijden</h2>
        <ul class="footer-hours">{hours}</ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span><span>© {datetime.date.today().year} {SITE['name']}</span> · <span>KVK {SITE['kvk']}</span> · <span>BTW {SITE['btw']}</span></span>
      <span class="footer-legal"><a href="/voorwaarden">Huisregels &amp; voorwaarden</a><a href="/privacy">Privacy &amp; cookies</a></span>
    </div>
    <p class="footer-note">De foto's op deze website zijn sfeerbeelden van de behandelingen. Ze tonen niet de salon of de medewerkers van Baitan.</p>
  </div>
</footer>
<aside class="quick-contact" aria-label="Snel contact">
<div class="mobile-bar" data-mobile-bar>
  <a class="btn btn-primary" {ext(SITE['booking_url'])}>Afspraak maken</a>
  <a class="mobile-bar-icon" {ext(SITE['whatsapp_question_url'])} aria-label="Stuur Baitan een WhatsApp-bericht">{WHATSAPP}</a>
  <a class="mobile-bar-icon" href="tel:{SITE['phone_href']}" aria-label="Bel Baitan">{icon('phone')}</a>
</div>
<a class="whatsapp-float" {ext(SITE['whatsapp_question_url'])} aria-label="Stuur Baitan een WhatsApp-bericht">{WHATSAPP}</a>
</aside>
<script src="/app.js?v={JS_V}" defer></script>
</body>
</html>"""


RESP_WIDTHS = [320, 480, 720, 1080, 1440, 1920, 2560]
MOBILE_MQ = "(max-width: 699px) and (orientation: portrait)"


def variants(name):
    """Beschikbare responsive breedtes (gemaakt met tools/optimize_images.py)."""
    d = ROOT / "assets" / "images" / "r"
    return [w for w in RESP_WIDTHS if (d / f"{name}-{w}.avif").exists() and (d / f"{name}-{w}.webp").exists()]


def srcset(name, ext):
    d = ROOT / "assets" / "images" / "r"
    return ", ".join(f"/assets/images/r/{name}-{w}.{ext}?v={fhash(d / f'{name}-{w}.{ext}')} {w}w" for w in variants(name))


def picture(name, alt, cls="", eager=False, sizes="100vw"):
    w, h = img_size(name)
    load = 'loading="eager" fetchpriority="high"' if eager else 'loading="lazy"'
    img = f'<img class="{cls}" src="/assets/images/{name}.webp" alt="{E(alt)}" width="{w}" height="{h}" {load} decoding="async">'
    if not variants(name):
        return img
    # Aparte mobiele uitsnede (bijv. 4:5 voor de hero) als <naam>-mobiel bestaat
    mob = f"{name}-mobiel"
    art = ""
    if variants(mob):
        art = (f'<source media="{MOBILE_MQ}" type="image/avif" srcset="{srcset(mob, "avif")}" sizes="100vw">'
               f'<source media="{MOBILE_MQ}" type="image/webp" srcset="{srcset(mob, "webp")}" sizes="100vw">')
    return (f'<picture>{art}<source type="image/avif" srcset="{srcset(name, "avif")}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{srcset(name, "webp")}" sizes="{sizes}">{img}</picture>')


def breadcrumbs(items):
    """items: [(naam, pad)] — laatste is de huidige pagina."""
    lis = []
    for i, (name, path) in enumerate(items):
        if i == len(items) - 1:
            lis.append(f'<li aria-current="page">{E(name)}</li>')
        else:
            lis.append(f'<li><a href="{path}">{E(name)}</a></li>')
    return f'<nav class="crumbs" aria-label="Kruimelpad"><ol>{"".join(lis)}</ol></nav>'


def crumb_schema(items):
    return {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": DOMAIN + p} for i, (n, p) in enumerate(items)
        ],
    }


def price_from(t):
    vals = t["solo"] or t["duo"]
    return min(vals)


def price_table(rows=None, caption="Prijzen per behandeling", show_duo=True, link=True):
    rows = rows or TREATMENTS
    head_cells = "".join(f'<th scope="col">{d} min</th>' for d in DURATIONS)
    body = []
    for t in rows:
        if t["id"] == "duo":
            continue
        name = f'<a href="/{t["slug"]}">{t["name"]}</a>' if (link and t["page"]) else t["name"]
        cells = []
        for i in range(len(DURATIONS)):
            duo = f'<span class="duo">duo {euro(t["duo"][i])}</span>' if (show_duo and t["duo"] and t["duo"][i]) else ""
            cells.append(f'<td><span class="solo">{euro(t["solo"][i])}</span>{duo}</td>')
        body.append(f'<tr><th scope="row">{name}</th>{"".join(cells)}</tr>')
    return f"""<div class="table-scroll"><table class="price-table">
<caption class="sr-only">{caption}</caption>
<thead><tr><th scope="col">Behandeling</th>{head_cells}</tr></thead>
<tbody>{"".join(body)}</tbody></table></div>"""


def duo_table():
    head_cells = "".join(f'<th scope="col">{d} min</th>' for d in DURATIONS)
    body = []
    for t in TREATMENTS:
        if t["id"] == "duo":
            continue
        if not t["duo"] or not all(t["duo"]):
            continue
        cells = "".join(f'<td><span class="solo">{euro(p)}</span></td>' for p in t["duo"])
        body.append(f'<tr><th scope="row">{t["name"]}</th>{cells}</tr>')
    return f"""<div class="table-scroll"><table class="price-table">
<caption class="sr-only">Prijzen duo-massage voor twee personen</caption>
<thead><tr><th scope="col">Duo-behandeling</th>{head_cells}</tr></thead>
<tbody>{"".join(body)}</tbody></table></div>"""


def treatment_rows(items, heading_level="h3"):
    out = []
    for t in items:
        href = f'/{t["slug"]}' if t["page"] else "/prijzen"
        label = "Bekijk behandeling" if t["page"] else "Bekijk prijzen"
        prefix = "voor twee, vanaf" if t["id"] == "duo" else "vanaf"
        out.append(f"""<li class="treatment">
  <a class="treatment-link" href="{href}">
    <span class="treatment-media">{picture(t['image'], t['alt'], sizes="(min-width: 760px) 150px, 88px")}</span>
    <span class="treatment-body">
      <{heading_level} class="treatment-name">{t['name']}</{heading_level}>
      <span class="treatment-text">{t['short']}</span>
      <span class="treatment-meta">60, 90 of 120 minuten</span>
    </span>
    <span class="treatment-price"><small>{prefix}</small>{euro(price_from(t))}</span>
    <span class="treatment-go" aria-hidden="true">{icon('arrow')}</span>
    <span class="sr-only">{label}</span>
  </a>
</li>""")
    return f'<ul class="treatment-list">{"".join(out)}</ul>'


def _fact_icon(text):
    t = text.lower()
    if "douch" in t:
        return "drop"
    if "pin" in t or "contant" in t or "betal" in t:
        return "card"
    if "parke" in t:
        return "car"
    return "shield"


def facilities_list():
    return '<ul class="facts">' + "".join(f'<li>{icon(_fact_icon(f))}<span><strong>{E(f)}</strong></span></li>' for f in FACILITIES) + "</ul>"


def hours_table():
    rows = "".join(f"<tr><th scope=\"row\">{h['label']}</th><td>{h['opens']} – {h['closes']}</td></tr>" for h in HOURS)
    return f'<table class="hours"><caption class="sr-only">Openingstijden</caption><tbody>{rows}</tbody></table>'


def faq_block(items):
    return '<div class="faq">' + "".join(
        f'<details class="faq-item"><summary>{E(q)}<span class="faq-icon" aria-hidden="true"></span></summary><div class="faq-answer"><p>{E(a)}</p></div></details>'
        for q, a in items
    ) + "</div>"


def week_hours_json():
    idx = {"Sunday": 0, "Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5, "Saturday": 6}
    week = [None] * 7
    for h in HOURS:
        for d in h["days"]:
            week[idx[d]] = [h["opens"], h["closes"]]
    return E(json.dumps(week))


def hours_short():
    def h(x):
        return x.split(":")[0].lstrip("0") if x.endswith(":00") else x
    a, b = HOURS
    return f"Ma–vr {h(a['opens'])}–{h(a['closes'])}\u00a0uur · za–zo {h(b['opens'])}–{h(b['closes'])}\u00a0uur"


def perks_section():
    items = []
    if GIFT.get("enabled", True):
        items.append(f"""<article class="perk">
          {icon('gift')}
          <h3>{E(GIFT.get('title', 'Cadeaubon'))}</h3>
          <p>{E(GIFT.get('text', ''))}</p>
          <a class="btn btn-outline btn-sm" {ext(SITE['whatsapp_gift_url'])}>{WHATSAPP} {E(GIFT.get('button') or 'Vraag via WhatsApp')}</a>
        </article>""")
    if LOYALTY.get("enabled", True):
        items.append(f"""<article class="perk">
          {icon('stamp')}
          <h3>{E(LOYALTY.get('title', 'Spaarkaart'))}</h3>
          <p>{E(LOYALTY.get('text', ''))}</p>
          <a class="btn btn-outline btn-sm" href="/contact">{E(LOYALTY.get('button') or 'Neem contact op')}</a>
        </article>""")
    if not items:
        return ""
    title = " en ".join(x for x, on in [("Cadeaubon", GIFT.get("enabled", True)), ("spaarkaart", LOYALTY.get("enabled", True))] if on)
    title = title[0].upper() + title[1:]
    return f"""<section class="section" id="cadeau" aria-labelledby="cadeau-title">
    <div class="wrap">
      <h2 id="cadeau-title" class="section-title">{title}</h2>
      <div class="perk-grid">{"".join(items)}</div>
    </div>
  </section>"""


DUO_CTA = ("Samen even helemaal tot rust komen?", "Kies in de online agenda een duo-behandeling en een tijd die jullie uitkomt.")


def side_card(gift=False):
    """Compacte boekkaart naast lopende tekst: wat het kost, wanneer en waar."""
    low = min(p for t in TREATMENTS for p in (t["solo"] or []) if p)
    second = (f'<a class="btn btn-outline btn-block" {ext(SITE["whatsapp_gift_url"])}>{WHATSAPP} Cadeaubon via WhatsApp</a>' if gift
              else '<a class="btn btn-outline btn-block" href="/prijzen">Alle prijzen</a>')
    return f"""<aside class="price-card side-card" aria-labelledby="side-title">
        <h2 id="side-title" class="price-card-title">{'Cadeaubon regelen' if gift else 'Direct een afspraak'}</h2>
        <ul class="side-facts">
          <li>{icon('clock')}<span data-open-status data-week="{week_hours_json()}">{hours_short()}</span></li>
          <li>{icon('pin')}<span>{SITE['street']}, <span class="nowrap">{SITE['city']}</span></span></li>
          <li>{icon('card')}<span>Massage vanaf €{low} voor 60 minuten</span></li>
        </ul>
        <div class="side-actions">
          <a class="btn btn-primary btn-block" {ext(SITE['booking_url'])}>Afspraak maken</a>
          {second}
        </div>
        <p class="price-card-meta">{icon('phone')} Liever bellen? <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></p>
      </aside>"""


def cta_band(title="Zin in een moment voor jezelf?", text="Kies in de online agenda een behandeling en een tijd die jou uitkomt."):
    return f"""<section class="cta-band">
  <div class="wrap cta-inner">
    <div>
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
    <div class="cta-actions">
      <a class="btn btn-light" {ext(SITE['booking_url'])}>Afspraak maken {icon('arrow')}</a>
      <a class="btn btn-ghost-light" href="tel:{SITE['phone_href']}">{icon('phone')} {SITE['phone_display']}</a>
    </div>
  </div>
</section>"""


def contact_block(h_tag="h2", title="Bezoek Baitan"):
    return f"""<div class="contact-grid">
  <div class="contact-details">
    <{h_tag}>{title}</{h_tag}>
    <ul class="contact-list">
      <li>{icon('pin')}<span><strong>Adres</strong>{SITE['street']}<br>{SITE['postal']} {SITE['city']}</span></li>
      <li>{icon('phone')}<span><strong>Telefoon</strong><a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></span></li>
      <li>{icon('mail')}<span><strong>E-mail</strong><a href="mailto:{SITE['email']}">{SITE['email']}</a></span></li>
      <li>{icon('clock')}<span><strong>Openingstijden</strong><span class="open-now" data-open-status data-week="{week_hours_json()}" data-short hidden></span>{hours_table()}</span></li>
    </ul>
    <div class="btn-row">
      <a class="btn btn-primary" {ext(SITE['route_url'])}>Route plannen</a>
      <a class="btn btn-outline" {ext(SITE['whatsapp_question_url'])}>{WHATSAPP} WhatsApp</a>
    </div>
  </div>
  <div class="map-consent" data-map="{E(SITE['map_embed_url'])}">
    <div class="map-consent-inner">
      {icon('pin')}
      <p class="map-title">Hollandsch Diep 71–73, Capelle aan den IJssel</p>
      <p>De kaart van Google Maps laden we pas als je daarvoor kiest. Laad je de kaart, dan maakt je browser verbinding met Google en kan Google cookies plaatsen.</p>
      <button class="btn btn-outline btn-sm" type="button" data-load-map>Kaart laden</button>
    </div>
  </div>
</div>"""


# ---------------------------------------------------------------- schema
def business_schema():
    offers = []
    for t in TREATMENTS:
        if t["id"] == "duo":
            continue
        url = f'{DOMAIN}/{t["slug"]}' if t["page"] else f"{DOMAIN}/prijzen"
        for i, d in enumerate(DURATIONS):
            offers.append({
                "@type": "Offer",
                "name": f'{t["name"]} {d} minuten',
                "price": str(t["solo"][i]),
                "priceCurrency": "EUR",
                "url": url,
                "itemOffered": {"@type": "Service", "name": t["name"]},
            })
            if not (t["duo"] and t["duo"][i]):
                continue
            offers.append({
                "@type": "Offer",
                "name": f'{t["name"]} duo {d} minuten',
                "price": str(t["duo"][i]),
                "priceCurrency": "EUR",
                "url": f"{DOMAIN}/duo-massage-capelle",
                "itemOffered": {"@type": "Service", "name": f'{t["name"]} duo'},
            })
    return {
        "@type": ["HealthAndBeautyBusiness", "DaySpa"],
        "@id": BIZ_ID,
        "name": SITE["name"],
        "url": DOMAIN + "/",
        "logo": {"@type": "ImageObject", "url": f"{DOMAIN}/logo/baitan-logo.png", "width": 600, "height": 815},
        "image": [f"{DOMAIN}/og-image.jpg", f"{DOMAIN}/assets/images/thaise-massage-capelle-aan-den-ijssel.webp"],
        "description": "Thaise massagesalon aan het Hollandsch Diep in Capelle aan den IJssel. Thaise massage, aromatherapie, sportmassage, hot stone, body scrub en duo-massage.",
        "telephone": SITE["phone_href"],
        "email": SITE["email"],
        "priceRange": f"€{min(p for x in TREATMENTS for p in (x['solo'] or []) if p)} – €{max(p for x in TREATMENTS for p in (x['duo'] or []) if p)}",
        "currenciesAccepted": "EUR",
        "paymentAccepted": "Cash, Debit Card",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": SITE["street"],
            "postalCode": SITE["postal"],
            "addressLocality": SITE["city"],
            "addressRegion": SITE["region"],
            "addressCountry": "NL",
        },
        "hasMap": SITE["maps_url"],
        "geo": {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]},
        "sameAs": [SITE["booking_url"]],
        "containedInPlace": {"@type": "Place", "name": f"{NEIGHBOURHOOD}, {SITE['city']}"},
        "areaServed": [{"@type": "City", "name": c} for c in ["Capelle aan den IJssel", "Rotterdam", "Krimpen aan den IJssel", "Nieuwerkerk aan den IJssel"]],
        "openingHoursSpecification": [
            {"@type": "OpeningHoursSpecification", "dayOfWeek": h["days"], "opens": h["opens"], "closes": h["closes"]} for h in HOURS
        ],
        "amenityFeature": [
            {"@type": "LocationFeatureSpecification", "name": "Douche", "value": True},
            {"@type": "LocationFeatureSpecification", "name": "Gratis parkeren", "value": True},
        ],
        "hasOfferCatalog": {"@type": "OfferCatalog", "name": "Massages", "itemListElement": offers},
        "potentialAction": {"@type": "ReserveAction", "target": SITE["booking_url"], "name": "Afspraak maken"},
    }


def website_schema():
    return {"@type": "WebSite", "@id": f"{DOMAIN}/#website", "url": DOMAIN + "/", "name": SITE["name"], "inLanguage": "nl-NL", "publisher": {"@id": BIZ_ID}}


def webpage_schema(path, title, description, page_type="WebPage"):
    return {
        "@type": page_type,
        "@id": f"{DOMAIN}{path}#webpage",
        "url": DOMAIN + path,
        "name": title,
        "description": description,
        "inLanguage": "nl-NL",
        "isPartOf": {"@id": f"{DOMAIN}/#website"},
        "about": {"@id": BIZ_ID},
        "dateModified": TODAY,
    }


def faq_schema(items):
    return {
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items],
    }


# ---------------------------------------------------------------- pages
def page_home():
    title = SEO.get("title") or "Thaise massage Capelle aan den IJssel | Baitan Thai Massage"
    desc = SEO.get("description") or ""
    thai = next((x for x in TREATMENTS if x["id"] == "thai"), None)
    home_faq = list(FAQ)
    if thai:
        home_faq.insert(0, price_faq(thai))
    home_faq.insert(1, ("Hoe lang duurt een massage bij Baitan?", "Je kiest zelf: elke behandeling is te boeken voor 60, 90 of 120 minuten. Kom een paar minuten van tevoren, zodat je rustig kunt beginnen."))
    home_faq = home_faq[:6]  # de rest staat op /veelgestelde-vragen
    schema = [business_schema(), website_schema(), webpage_schema("/", title, desc), faq_schema(home_faq)]
    quiz = []
    for qi, step in enumerate(QUIZ):
        buttons = "".join(f'<button type="button" class="quiz-option" data-o="{oi}" aria-pressed="false">{E(o["label"])}</button>' for oi, o in enumerate(step["options"]))
        quiz.append(f'<fieldset class="quiz-step" data-step="{qi}"{"" if qi == 0 else " hidden"}><legend>{E(step["q"]["self"])}</legend><div class="quiz-options">{buttons}</div></fieldset>')
    duo_t = BY_ID.get("duo")
    quiz_data = {
        "steps": [{"q": st["q"], "options": [{k: v for k, v in o.items() if k != "label"} for o in st["options"]]} for st in QUIZ],
        "order": QUIZ_ORDER,
        "durations": DURATIONS,
        "duoUrl": f'/{duo_t["slug"]}' if duo_t and duo_t["page"] else "/prijzen",
        "t": {t["id"]: {"name": t["name"], "lname": lname(t["name"]), "text": t["short"], "url": f'/{t["slug"]}' if t["page"] else "/prijzen", "solo": t["solo"], "duo": t["duo"]} for t in TREATMENTS if t["id"] in QUIZ_ORDER},
    }
    gift_btn = f'<a class="btn btn-outline btn-sm" {ext(SITE["whatsapp_gift_url"])}>{WHATSAPP} Vraag via WhatsApp</a>'
    body = f"""{head(title, desc, "/", schema=schema, preload_img=Path(HERO.get('image', 'thaise-massage-capelle-aan-den-ijssel')).stem)}
<body class="page-home">
{header()}
<main id="main">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-media">{picture(Path(HERO.get('image', 'thaise-massage-capelle-aan-den-ijssel')).stem, HERO.get('imageAlt', ''), 'hero-img', eager=True, sizes="100vw")}</div>
    <div class="wrap hero-inner">
      <div class="hero-copy">
        <h1 id="hero-title">{E(HERO.get('title', ''))}</h1>
        <p class="hero-lead">{E(HERO.get('text', ''))}</p>
        <div class="btn-row">
          <a class="btn btn-light" {ext(SITE['booking_url'])}>{E(HERO.get('primaryButton') or 'Afspraak maken')} {icon('arrow')}</a>
          <a class="btn btn-ghost-light" href="#behandelingen">{E(HERO.get('secondaryButton') or 'Bekijk behandelingen')}</a>
        </div>
      </div>
      <ul class="hero-facts" aria-label="In het kort">
        <li><a {ext(SITE['maps_url'])}>{stars()}<span><strong>{SITE['rating']}</strong> uit {SITE['review_count']} Google-reviews</span></a></li>
        <li>{icon('clock')}<span data-open-status data-week="{week_hours_json()}">{hours_short()}</span></li>
        <li>{icon('car')}<span>Gratis parkeren in de buurt</span></li>
      </ul>
    </div>
  </section>

  <section class="section" id="behandelingen" aria-labelledby="behandelingen-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="behandelingen-title">Kies je massage</h2>
        <p>Elke behandeling boek je voor 60, 90 of 120 minuten. Alleen, of samen als duo-massage.</p>
      </div>
      {treatment_rows(TREATMENTS)}
    </div>
  </section>

  <section class="section section-tint" id="massagekeuze" aria-labelledby="quiz-title">
    <div class="wrap quiz-grid">
      <div class="quiz-intro">
        <h2 id="quiz-title">Twijfel je welke massage bij je past?</h2>
        <p>Vijf korte vragen over wat je zoekt. Je krijgt direct een advies met uitleg, de duur en de prijs.</p>
        <p class="quiz-note">Twijfel je daarna nog? Bij Baitan bespreek je vooraf altijd de druk en waar de nadruk mag liggen.</p>
        <button class="btn btn-primary quiz-start" type="button" data-quiz-open aria-controls="quiz-panel" aria-expanded="false" hidden>Start de massagekeuze {icon('arrow')}</button>
      </div>
      <div class="quiz" id="quiz-panel" data-quiz='{E(json.dumps(quiz_data, ensure_ascii=False))}'>
        <div class="quiz-progress">
          <button class="quiz-back" type="button" data-quiz-back hidden>{icon('arrow')}<span>Vorige</span></button>
          <span data-quiz-label aria-live="polite">Vraag 1 van {len(QUIZ)}</span><span class="quiz-track" aria-hidden="true"><span data-quiz-bar></span></span>
        </div>
        {"".join(quiz)}
        <div class="quiz-result" data-quiz-result hidden tabindex="-1" aria-labelledby="quiz-result-title">
          <p class="quiz-result-label" data-quiz-kicker>Jouw beste match</p>
          <h3 id="quiz-result-title" data-quiz-title></h3>
          <p class="quiz-meta" data-quiz-meta></p>
          <p data-quiz-text></p>
          <div class="quiz-why">
            <p class="quiz-why-title">Waarom dit past</p>
            <ul data-quiz-why></ul>
          </div>
          <div class="btn-row">
            <a class="btn btn-primary" {ext(SITE['booking_url'])} data-quiz-book>Afspraak maken</a>
            <a class="btn btn-primary" {ext(SITE['whatsapp_gift_url'])} data-quiz-gift hidden>Cadeaubon via WhatsApp</a>
            <a class="btn btn-outline" href="/massages" data-quiz-link>Bekijk behandeling</a>
          </div>
          <p class="quiz-alt" data-quiz-alt hidden>Ook een goede keuze: <a href="/massages" data-quiz-alt-link></a></p>
          <button class="text-btn" type="button" data-quiz-restart>Opnieuw beginnen</button>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="prijzen" aria-labelledby="prijzen-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="prijzen-title">Prijzen</h2>
        <p>Prijs per persoon. Onder elke prijs zie je wat dezelfde massage samen (duo, twee personen) kost.</p>
      </div>
      {price_table()}
      <div class="price-foot">
        <p>Betalen kan met pin of contant. Annuleren is kosteloos tot 24 uur vooraf.</p>
        <a class="btn btn-primary" {ext(SITE['booking_url'])}>Bekijk vrije tijden {icon('arrow')}</a>
      </div>
    </div>
  </section>

  <section class="section section-tint" id="over" aria-labelledby="over-title">
    <div class="wrap about-grid">
      <figure class="about-media">{picture(Path(ABOUT.get('image', 'thaise-begroeting-wai')).stem, ABOUT.get('imageAlt', ''), sizes="(min-width: 900px) 84vw, 100vw")}</figure>
      <div class="about-copy">
        <h2 id="over-title">{E(ABOUT.get('title', 'Over Baitan'))}</h2>
        <p>{E(ABOUT.get('text', ''))}</p>
        {facilities_list()}
      </div>
    </div>
  </section>

{perks_section()}

  <section class="section section-dark" id="reviews" aria-labelledby="reviews-title">
    <div class="wrap reviews">
      <div class="rating">
        <p class="rating-score" aria-hidden="true">{SITE['rating']}</p>
        {stars()}
      </div>
      <div class="reviews-copy">
        <h2 id="reviews-title">Gemiddeld {SITE['rating']} uit 5 op Google</h2>
        <p>Op basis van {SITE['review_count']} Google-reviews (stand {SITE['review_as_of']}). De reviews staan op Google en worden niet door Baitan gecontroleerd. Lees ze zelf, of laat na je bezoek een review achter.</p>
        <div class="btn-row">
          <a class="btn btn-light" {ext(SITE['maps_url'])}>Lees de reviews</a>
          <a class="btn btn-ghost-light" {ext(SITE['review_write_url'])}>Schrijf een review</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section local" id="locatie" aria-labelledby="locatie-title">
    <div class="wrap local-grid">
      <h2 id="locatie-title">Massage in {SITE['city']}</h2>
      <div class="local-copy">
        <p>Baitan Thai Massage zit aan het {SITE['street']} in de wijk {NEIGHBOURHOOD}, {SITE['city']}. Je parkeert gratis in de directe omgeving en loopt zo naar binnen.</p>
        <p>Ook vanuit {", ".join(NEARBY[:-1])} en {NEARBY[-1]} ben je snel in de salon. We zijn zeven dagen per week open: {hours_short().replace("Ma–vr", "maandag tot en met vrijdag").replace("za–zo", "zaterdag en zondag").replace(" · ", ", ")}.</p>
        <p class="local-links"><a class="link" href="/thaise-massage-capelle-aan-den-ijssel">Thaise massage {icon('arrow')}</a><a class="link" href="/prijzen">Prijzen {icon('arrow')}</a><a class="link" {ext(SITE['route_url'])}>Route plannen {icon('arrow')}</a></p>
      </div>
    </div>
  </section>

  <section class="section section-tint" id="massagegids" aria-labelledby="kb-title">
    <div class="wrap">
      <div class="section-head"><h2 id="kb-title">Meer weten over massage</h2><p><a class="link" href="/massagegids">Naar de massagegids {icon('arrow')}</a></p></div>
      {article_cards(ARTICLES[:3])}
    </div>
  </section>

  <section class="section" id="faq" aria-labelledby="faq-title">
    <div class="wrap faq-grid">
      <div>
        <h2 id="faq-title">Veelgestelde vragen</h2>
        <p>Staat je vraag er niet bij? Bel <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a> of stuur een <a {ext(SITE['whatsapp_question_url'])}>WhatsApp-bericht</a>.</p>
        <p><a class="link" href="/veelgestelde-vragen">Alle veelgestelde vragen {icon('arrow')}</a></p>
      </div>
      {faq_block(home_faq)}
    </div>
  </section>

  <section class="section section-tint" id="contact" aria-labelledby="contact-title">
    <div class="wrap">
      {contact_block().replace('<h2>', '<h2 id="contact-title">', 1)}
    </div>
  </section>
</main>
{footer()}"""
    return body


def hero_prices(t):
    prices = t["duo"] if t["id"] == "duo" else t["solo"]
    if not prices:
        return ""
    items = "".join(f"<li><span>{m} min</span><strong>€{p}</strong></li>" for m, p in zip(t["durations"], prices) if p)
    if t["id"] == "duo":
        return f'<p class="hero-prices-label">Voor twee personen samen, vanaf</p><ul class="hero-prices" aria-label="Prijs voor twee personen samen, vanaf">{items}</ul>'
    return f'<ul class="hero-prices" aria-label="Prijs per persoon">{items}</ul>'


def page_treatment(t):
    path = f'/{t["slug"]}'
    crumbs = [("Home", "/"), ("Behandelingen", "/massages"), (t["name"], path)]
    others = [o for o in TREATMENTS if o["id"] != t["id"]]
    is_duo = t["id"] == "duo"
    prices_html = duo_table() if is_duo else price_table([t], caption=f'Prijzen {t["name"]}', link=False)
    price_note = "Prijs voor twee personen samen." if is_duo else "Prijs per persoon. Onder elke prijs staat de prijs voor twee personen samen (duo)."
    faq_items = [price_faq(t), (f"Hoe lang duurt een {lname(t['name'])}?", "Je kiest zelf voor 60, 90 of 120 minuten. Twijfel je? Begin met 60 minuten en kies de volgende keer langer.")] + [FAQ[i] for i in (0, 4, 2) if i < len(FAQ)]
    service = {
        "@type": "Service",
        "@id": f"{DOMAIN}{path}#service",
        "name": t["name"],
        "serviceType": t["name"],
        "description": t["lead"],
        "url": DOMAIN + path,
        "image": f'{DOMAIN}/assets/images/{t["image"]}.webp',
        "provider": {"@id": BIZ_ID},
        "areaServed": {"@type": "City", "name": SITE["city"]},
        "offers": [
            {"@type": "Offer", "name": f'{t["name"]} {d} minuten', "price": str((t["duo"] if is_duo else t["solo"])[i]), "priceCurrency": "EUR", "url": SITE["booking_url"]}
            for i, d in enumerate(DURATIONS)
        ],
    }
    schema = [business_schema(), website_schema(), webpage_schema(path, t["seo_title"], t["seo_description"]), service, crumb_schema(crumbs), faq_schema(faq_items)]
    steps = "".join(f'<li><span class="step-n" aria-hidden="true">{i + 1}</span><span><strong>{a}</strong>{b}</span></li>' for i, (a, b) in enumerate(t["steps"]))
    body_p = "".join(f"<p>{p}</p>" for p in t["body"])
    return f"""{head(t['seo_title'], t['seo_description'], path, schema=schema, preload_img=t['image'], preload_sizes="(min-width: 900px) 42vw, 100vw")}
<body>
{header('/massages')}
<main id="main">
  <section class="page-hero" aria-labelledby="page-title">
    <div class="wrap page-hero-grid">
      <div>
        {breadcrumbs(crumbs)}
        <h1 id="page-title">{t['h1']}</h1>
        <p class="page-lead">{t['lead']}</p>
        {hero_prices(t)}
        <div class="btn-row">
          <a class="btn btn-primary" {ext(SITE['booking_url'])}>Afspraak maken {icon('arrow')}</a>
          <a class="btn btn-outline hide-mobile" href="#prijs">Prijzen bekijken</a>
        </div>
      </div>
      <figure class="page-hero-media">{picture(t['image'], t['alt'], eager=True, sizes="(min-width: 900px) 42vw, 100vw")}</figure>
    </div>
  </section>

  <section class="section" aria-labelledby="over-behandeling">
    <div class="wrap detail-grid">
      <div class="prose">
        <h2 id="over-behandeling">Zo verloopt je behandeling</h2>
        {body_p}
        <ol class="steps">{steps}</ol>
      </div>
      <aside class="price-card" id="prijs" aria-labelledby="prijs-title">
        <h2 id="prijs-title" class="price-card-title">Duur en prijs</h2>
        {prices_html}
        <p class="price-card-note">{price_note}</p>
        <a class="btn btn-primary btn-block" {ext(SITE['booking_url'])}>Afspraak maken</a>
        <p class="price-card-meta">{icon('phone')} Liever bellen? <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a></p>
      </aside>
    </div>
  </section>

  <section class="section section-tint" aria-labelledby="goed-title">
    <div class="wrap faq-grid">
      <div>
        <h2 id="goed-title">Goed om te weten</h2>
        <p>Baitan zit aan het Hollandsch Diep 71–73 in Capelle aan den IJssel. Parkeren is gratis in de directe omgeving.</p>
        {facilities_list()}
      </div>
      {faq_block(faq_items)}
    </div>
  </section>

  <section class="section" aria-labelledby="ook-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="ook-title">Andere behandelingen</h2>
        <p><a class="link" href="/massages">Alle behandelingen {icon('arrow')}</a></p>
      </div>
      {treatment_rows(others)}
    </div>
  </section>
  {cta_band(*DUO_CTA) if is_duo else cta_band()}
</main>
{footer()}"""


def page_massages():
    path = "/massages"
    title = "Massages in Capelle aan den IJssel | Baitan Thai Massage"
    desc = "Alle massages van Baitan in Capelle aan den IJssel: Thaise massage, aromatherapie, sportmassage, hot stone, body scrub en duo-massage. 60, 90 of 120 minuten."
    crumbs = [("Home", "/"), ("Behandelingen", path)]
    itemlist = {
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": t["name"], "url": f'{DOMAIN}/{t["slug"]}'} for i, t in enumerate(PAGES)
        ],
    }
    schema = [business_schema(), website_schema(), webpage_schema(path, title, desc, "CollectionPage"), crumb_schema(crumbs), itemlist]
    return f"""{head(title, desc, path, schema=schema)}
<body>
{header(path)}
<main id="main">
  <section class="page-hero page-hero-plain" aria-labelledby="page-title">
    <div class="wrap">
      {breadcrumbs(crumbs)}
      <h1 id="page-title">Massages in Capelle aan den IJssel</h1>
      <p class="page-lead">Van traditioneel Thais tot warme stenen. Elke behandeling boek je voor 60, 90 of 120 minuten, alleen of samen met iemand.</p>
    </div>
  </section>
  <section class="section section-flush-top" aria-label="Alle behandelingen">
    <div class="wrap">{treatment_rows(TREATMENTS, 'h2')}</div>
  </section>
  <section class="section section-flush-top" aria-labelledby="voorwie-title">
    <div class="wrap">
      <div class="section-head"><h2 id="voorwie-title">Welke massage past bij jou?</h2><a class="btn btn-outline" href="/#massagekeuze">Doe de massagekeuze {icon('arrow')}</a></div>
      <ul class="pill-links">{"".join(f'<li><a href="/{lp["slug"]}">{E(lp["h1"].replace(" in Capelle aan den IJssel", ""))} {icon("arrow")}</a></li>' for lp in LANDINGS if lp.get("kind") != "basis")}<li><a href="/cadeaubon">Massage cadeau geven {icon("arrow")}</a></li></ul>
    </div>
  </section>
  <section class="section section-tint" aria-labelledby="prijzen-title">
    <div class="wrap">
      <div class="section-head">
        <h2 id="prijzen-title">Prijzen in één oogopslag</h2>
        <p>Prijs per persoon, met daaronder de prijs voor twee personen samen.</p>
      </div>
      {price_table()}
    </div>
  </section>
  {cta_band()}
</main>
{footer()}"""


def page_prijzen():
    path = "/prijzen"
    title = "Prijzen massage Capelle aan den IJssel | Baitan Thai Massage"
    desc = "Bekijk alle prijzen van Baitan Thai Massage in Capelle aan den IJssel. Massages van 60, 90 en 120 minuten vanaf €65, duo-massage vanaf €125 voor twee."
    crumbs = [("Home", "/"), ("Prijzen", path)]
    price_faqs = [price_faq(t) for t in TREATMENTS if t["solo"] or t["id"] == "duo"]
    price_faqs += [
        ("Welke duur kies ik: 60, 90 of 120 minuten?", "Met 60 minuten heb je een fijne, complete massage. Met 90 of 120 minuten is er meer tijd voor je hele lichaam en voor plekken waar je veel spanning voelt. Lees meer in het artikel over de duur van een massage."),
        ("Kan ik een massage cadeau geven?", "Ja. Cadeaubonnen zijn verkrijgbaar in de salon of te regelen via WhatsApp. Je kunt elke behandeling cadeau geven."),
    ]
    schema = [business_schema(), website_schema(), webpage_schema(path, title, desc), crumb_schema(crumbs), faq_schema(price_faqs)]
    notes = [
        ("Duo-massage", "Met z'n tweeën tegelijk een massage. De duo-prijs geldt voor twee personen samen."),
        ("Betalen", "Met pin of contant in de salon."),
        ("Btw", "Alle prijzen zijn inclusief btw."),
        ("Annuleren", "Kosteloos tot 24 uur vooraf. Daarna vindt geen restitutie plaats."),
        ("Spaarkaart", "Per 60 minuten één stempel. Bij 10 stempels krijg je 60 minuten massage naar keuze."),
    ]
    notes_html = "".join(f"<li><strong>{a}</strong><span>{b}</span></li>" for a, b in notes)
    return f"""{head(title, desc, path, schema=schema)}
<body>
{header(path)}
<main id="main">
  <section class="page-hero page-hero-plain" aria-labelledby="page-title">
    <div class="wrap">
      {breadcrumbs(crumbs)}
      <h1 id="page-title">Prijzen</h1>
      <p class="page-lead">Alle massages zijn te boeken voor 60, 90 of 120 minuten. Je ziet de prijs per persoon en daaronder de prijs voor een duo-massage.</p>
    </div>
  </section>
  <section class="section section-flush-top" aria-label="Prijslijst">
    <div class="wrap">
      {price_table()}
      <ul class="notes">{notes_html}</ul>
      <div class="price-foot">
        <p>De online agenda toont altijd de actuele prijzen en vrije tijden.</p>
        <a class="btn btn-primary" {ext(SITE['booking_url'])}>Afspraak maken {icon('arrow')}</a>
      </div>
    </div>
  </section>
  <section class="section section-tint" aria-labelledby="faq-title">
    <div class="wrap faq-grid">
      <div><h2 id="faq-title">Vragen over prijzen</h2><p>Twijfel je over de duur? Lees <a href="/massagegids/hoe-lang-moet-een-massage-duren">hoe lang een massage moet duren</a> of bekijk <a href="/veelgestelde-vragen">alle vragen</a>.</p></div>
      {faq_block(price_faqs)}
    </div>
  </section>
  {cta_band()}
</main>
{footer()}"""


def page_contact():
    path = "/contact"
    title = "Contact en route | Baitan Thai Massage Capelle"
    desc = "Baitan Thai Massage, Hollandsch Diep 71–73 in Capelle aan den IJssel. Bel 06 83 936 366, stuur een WhatsApp of plan je route. Gratis parkeren."
    crumbs = [("Home", "/"), ("Contact", path)]
    schema = [business_schema(), website_schema(), webpage_schema(path, title, desc, "ContactPage"), crumb_schema(crumbs)]
    return f"""{head(title, desc, path, schema=schema)}
<body>
{header(path)}
<main id="main">
  <section class="page-hero page-hero-plain" aria-labelledby="page-title">
    <div class="wrap">
      {breadcrumbs(crumbs)}
      <h1 id="page-title">Contact en route</h1>
      <p class="page-lead">Je vindt Baitan aan het Hollandsch Diep in Capelle aan den IJssel. Parkeren is gratis in de directe omgeving.</p>
    </div>
  </section>
  <section class="section section-flush-top">
    <div class="wrap">{contact_block('h2', 'Gegevens')}</div>
  </section>
  <section class="section section-tint" aria-labelledby="faq-title">
    <div class="wrap faq-grid">
      <div><h2 id="faq-title">Veelgestelde vragen</h2><p>Over annuleren, betalen en parkeren.</p></div>
      {faq_block(FAQ[:5])}
    </div>
  </section>
  {cta_band()}
</main>
{footer()}"""


LEGAL_UPDATED = "2026-10-09"  # aanpassen als de tekst van voorwaarden of privacy wijzigt


def page_legal(kind):
    if kind == "voorwaarden":
        path, title, h1 = "/voorwaarden", "Huisregels en voorwaarden | Baitan Thai Massage", "Huisregels en voorwaarden"
        desc = "Huisregels en algemene voorwaarden van Baitan Thai Massage: reserveren, annuleren, te laat komen, gezondheid en cadeaubonnen."
        sections = [
            ("Algemeen", ["Deze voorwaarden gelden voor diensten, boekingen en overeenkomsten van Baitan Thai Massage. Door een afspraak te maken ga je akkoord met deze voorwaarden."]),
            ("Diensten", ["Baitan biedt ontspannings- en wellnessmassages. De behandelingen zijn niet medisch van aard en vervangen geen behandeling door een arts of specialist."]),
            ("Reservering en betaling", ["Je maakt een afspraak online via Salonized, telefonisch, via WhatsApp of in de salon. Je betaalt in de salon met pin of contant. Vraagt de online agenda bij het boeken om een vooruitbetaling, dan zie je dat voordat je de boeking bevestigt.", "Alle prijzen zijn inclusief btw."]),
            ("Annuleren en verzetten", None),
            ("Herroepingsrecht", ["Een massage is een vrijetijdsdienst op een vaste datum en tijd. Voor afspraken die je online, telefonisch of via WhatsApp maakt, geldt daarom geen wettelijk herroepingsrecht van 14 dagen. Je kunt wel kosteloos annuleren tot 24 uur vóór de afspraak."]),
            ("Te laat komen", ["Bij te laat komen kan de behandeltijd worden ingekort. De volledige kosten van de geboekte behandeling blijven verschuldigd."]),
            ("Gezondheid", ["Meld relevante gezondheidsinformatie, waaronder blessures, zwangerschap of medicijngebruik, vóór de behandeling. Baitan kan een behandeling weigeren wanneer gezondheidsrisico's worden ingeschat."]),
            ("Gedrag en hygiëne", ["Respectvol en hygiënisch gedrag is verplicht. Ongepast gedrag kan leiden tot onmiddellijke beëindiging van de behandeling zonder restitutie. Erotische of seksuele verzoeken zijn niet toegestaan."]),
            ("Aansprakelijkheid", ["Laat waardevolle spullen bij voorkeur thuis. Baitan is niet aansprakelijk voor verlies, diefstal of beschadiging van persoonlijke eigendommen, tenzij dit het gevolg is van opzet of grove nalatigheid van Baitan of haar medewerkers.", "Is Baitan voor andere schade aansprakelijk, dan is die aansprakelijkheid beperkt tot het bedrag dat de aansprakelijkheidsverzekering uitkeert, of als de verzekering niet uitkeert, tot het bedrag van de geboekte behandeling. Deze beperking geldt niet bij opzet of grove nalatigheid en niet bij letselschade."]),
            ("Cadeaubonnen", ["Een cadeaubon is minimaal 2 jaar geldig vanaf de datum van aankoop. De uiterste datum staat op de bon. Cadeaubonnen zijn niet inwisselbaar voor geld."]),
            ("Overmacht", ["Moet Baitan een afspraak annuleren of verzetten door ziekte, een storing of een andere onvoorziene omstandigheid, dan laten we je dat zo snel mogelijk weten. Je kiest dan zelf: een nieuwe afspraak of volledige terugbetaling van wat je al hebt betaald."]),
            ("Foto's op deze website", ["De foto's op deze website zijn kunstmatig gegenereerde sfeerbeelden van de behandelingen. Ze tonen niet de salon of de medewerkers van Baitan."]),
            ("Toepasselijk recht", ["Op de dienstverlening is Nederlands recht van toepassing."]),
        ]
        cancel = "<ul><li>Kosteloos annuleren tot 24 uur vóór de afspraak.</li><li>Binnen 24 uur vindt geen restitutie plaats.</li><li>Een afspraak kan één keer kosteloos worden verzet.</li><li>Bij een no-show vervalt de afspraak zonder terugbetaling.</li></ul>"
    else:
        path, title, h1 = "/privacy", "Privacy en cookies | Baitan Thai Massage", "Privacy en cookies"
        desc = "Hoe Baitan Thai Massage omgaat met je gegevens: contact, online boeken via Salonized, Google Maps en cookies."
        sections = [
            ("Wie is verantwoordelijk?", [f"Baitan Thai Massage, {SITE['street']}, {SITE['postal']} {SITE['city']} (KVK {SITE['kvk']}), is verantwoordelijk voor de verwerking van je persoonsgegevens. Vragen? Mail naar <a href=\"mailto:{SITE['email']}\">{SITE['email']}</a> of bel <a href=\"tel:{SITE['phone_href']}\">{SITE['phone_display']}</a>."]),
            ("Welke gegevens we gebruiken en waarom", ["<ul>"
                "<li><strong>Afspraken</strong> (online via Salonized, telefonisch, via WhatsApp of in de salon): naam, telefoonnummer, e-mailadres, behandeling, datum en tijd en betaalgegevens. Om je afspraak in te plannen, te bevestigen, je eraan te herinneren en af te rekenen. Grondslag: uitvoering van de overeenkomst (art. 6 lid 1 sub b AVG).</li>"
                "<li><strong>Contact</strong> (telefoon, WhatsApp, e-mail): je contactgegevens en je bericht, om je vraag te beantwoorden. Grondslag: uitvoering van de overeenkomst of ons gerechtvaardigd belang om vragen te beantwoorden (art. 6 lid 1 sub b en f AVG).</li>"
                "<li><strong>Gezondheid</strong>: vertel je ons over blessures, zwangerschap of medicijngebruik, dan gebruiken we dat alleen om de behandeling veilig af te stemmen. We leggen dit alleen vast als jij daar uitdrukkelijk toestemming voor geeft (art. 9 lid 2 sub a AVG). Je kunt die toestemming altijd intrekken.</li>"
                "<li><strong>Administratie</strong>: betalingen en verkochte cadeaubonnen, omdat de wet dat verplicht (art. 6 lid 1 sub c AVG).</li>"
                "<li><strong>Website</strong>: bij elk bezoek verwerkt onze hostingpartij technische gegevens zoals IP-adres, browser en tijdstip, om de website veilig en werkend te houden. Grondslag: gerechtvaardigd belang (art. 6 lid 1 sub f AVG).</li>"
                "</ul>"]),
            ("Wie je gegevens ontvangt", ["<ul>"
                "<li>Salonized: online agenda en klantadministratie, in opdracht van Baitan.</li>"
                "<li>Vercel Inc.: hosting van deze website.</li>"
                "<li>WhatsApp (Meta): alleen als je ons via WhatsApp benadert. WhatsApp is zelf verantwoordelijk voor de eigen verwerking.</li>"
                "<li>Google: alleen als je zelf de kaart laadt of op een Google-link klikt.</li>"
                "<li>Onze boekhouder en de Belastingdienst, voor de administratie.</li>"
                "</ul>", "We verkopen je gegevens nooit."]),
            ("Doorgifte buiten de EU", ["Vercel, Google en Meta kunnen gegevens in de Verenigde Staten verwerken. Dat gebeurt op basis van het EU-VS Data Privacy Framework of de standaardcontractbepalingen van de Europese Commissie."]),
            ("Hoe lang we je gegevens bewaren", ["<ul>"
                "<li>Klant- en afspraakgegevens: tot 2 jaar na je laatste afspraak.</li>"
                "<li>Berichten via WhatsApp of e-mail: tot 1 jaar na het laatste contact.</li>"
                "<li>Gezondheidsinformatie: tot je je toestemming intrekt, en uiterlijk 2 jaar na je laatste afspraak.</li>"
                "<li>Administratie: 7 jaar (wettelijke bewaarplicht).</li>"
                "<li>Technische websitegegevens: zo kort mogelijk, alleen zolang dat nodig is voor beveiliging en storingen.</li>"
                "</ul>"]),
            ("Google Maps", ["De kaart van Google Maps wordt pas geladen nadat je op ‘Kaart laden’ klikt. Daarna maakt je browser verbinding met Google en kan Google cookies plaatsen en gegevens verwerken volgens het eigen privacy- en cookiebeleid."]),
            ("Cookies", ["Deze website plaatst geen marketing- of analyticscookies. Lettertypes worden vanaf onze eigen server geladen, niet via Google. Externe diensten zoals Salonized, WhatsApp en Google Maps gebruiken pas cookies als je ze zelf opent."]),
            ("Je rechten", [f"Je hebt recht op inzage, correctie, verwijdering, beperking van de verwerking en overdracht van je gegevens. Je kunt bezwaar maken tegen verwerking op basis van gerechtvaardigd belang, en een gegeven toestemming altijd intrekken. Stuur je verzoek naar <a href=\"mailto:{SITE['email']}\">{SITE['email']}</a>; we reageren binnen een maand.", "Ben je het niet eens met hoe we met je gegevens omgaan, dan kun je een klacht indienen bij de <a href=\"https://autoriteitpersoonsgegevens.nl\" rel=\"noopener\">Autoriteit Persoonsgegevens</a>."]),
        ]
        cancel = ""
    crumbs = [("Home", "/"), (h1, path)]
    schema = [website_schema(), webpage_schema(path, title, desc), crumb_schema(crumbs)]
    robots = "noindex,follow"
    secs = []
    for h, ps in sections:
        inner = cancel if ps is None else "".join(p if p.startswith("<ul") else f"<p>{p}</p>" for p in ps)
        secs.append(f"<h2>{h}</h2>{inner}")
    contact = f"<h2>Contact</h2><p>{SITE['name']}, {SITE['street']}, {SITE['postal']} {SITE['city']}. Telefoon <a href=\"tel:{SITE['phone_href']}\">{SITE['phone_display']}</a>, e-mail <a href=\"mailto:{SITE['email']}\">{SITE['email']}</a>. KVK {SITE['kvk']}.</p>"
    return f"""{head(title, desc, path, schema=schema, robots=robots)}
<body>
{header()}
<main id="main">
  <section class="page-hero page-hero-plain" aria-labelledby="page-title">
    <div class="wrap">
      {breadcrumbs(crumbs)}
      <h1 id="page-title">{h1}</h1>
      <p class="legal-updated">Laatst bijgewerkt op {nl_date(LEGAL_UPDATED)}</p>
    </div>
  </section>
  <section class="section section-flush-top"><div class="wrap"><div class="prose legal">{"".join(secs)}{contact}</div></div></section>
</main>
{footer()}"""


def page_404():
    title = "Pagina niet gevonden | Baitan Thai Massage"
    desc = "Deze pagina bestaat niet (meer). Bekijk de massages en prijzen van Baitan Thai Massage."
    return f"""{head(title, desc, "/404", robots="noindex,follow")}
<body>
{header()}
<main id="main">
  <section class="page-hero page-hero-plain notfound">
    <div class="wrap">
      <h1>Deze pagina bestaat niet</h1>
      <p class="page-lead">Misschien is de link veranderd. Kies hieronder waar je naartoe wilt.</p>
      <div class="btn-row">
        <a class="btn btn-primary" href="/">Naar de homepage</a>
        <a class="btn btn-outline" href="/massages">Behandelingen</a>
        <a class="btn btn-outline" href="/prijzen">Prijzen</a>
      </div>
    </div>
  </section>
</main>
{footer()}"""


# ---------------------------------------------------------------- markdown-content
import re as _re

CONTENT = ROOT / "content"


def tokens(text):
    """Vervangt {{...}} door actuele gegevens uit de data, zodat teksten nooit verouderen."""
    a, b = HOURS
    def h(x):
        return x.split(":")[0].lstrip("0") if x.endswith(":00") else x
    repl = {
        "openingstijden": f"maandag tot en met vrijdag {h(a['opens'])}–{h(a['closes'])}\u00a0uur, zaterdag en zondag {h(b['opens'])}–{h(b['closes'])}\u00a0uur",
        "adres": f"{SITE['street']}, {SITE['postal']} {SITE['city']}",
        "telefoon": SITE["phone_display"],
    }
    return _re.sub(r"\{\{(\w+)\}\}", lambda m: repl.get(m.group(1), m.group(0)), text)


def _inline(s):
    s = E(s, quote=False)
    s = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = _re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<em>\1</em>", s)

    def link(m):
        label, href = m.group(1), m.group(2)
        if href.startswith("http"):
            return f'<a href="{href}" target="_blank" rel="noopener">{label}</a>'
        return f'<a href="{href}">{label}</a>'
    return _re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)", link, s)


def md(text):
    """Kleine, voorspelbare Markdown-renderer: koppen, alinea's, lijsten, tabellen, vet, cursief, links."""
    out, lines, i = [], tokens(text).strip().split("\n"), 0
    toc = []
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1
            continue
        if ln.startswith("### "):
            out.append(f"<h3>{_inline(ln[4:])}</h3>")
            i += 1
        elif ln.startswith("## "):
            title = ln[3:].strip()
            anchor = _re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            toc.append((anchor, title))
            out.append(f'<h2 id="{anchor}">{_inline(title)}</h2>')
            i += 1
        elif ln.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(_re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            head, body = rows[0], rows[1:]
            th = "".join(f'<th scope="col">{_inline(c)}</th>' for c in head)
            trs = "".join("<tr>" + "".join((f'<th scope="row">{_inline(c)}</th>' if j == 0 else f"<td>{_inline(c)}</td>") for j, c in enumerate(r)) + "</tr>" for r in body)
            out.append(f'<div class="table-scroll" tabindex="0" role="region" aria-label="Vergelijkingstabel"><table class="compare-table"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>')
        elif _re.match(r"^(- |\d+\. )", ln):
            ordered = bool(_re.match(r"^\d+\. ", ln))
            items = []
            while i < len(lines) and _re.match(r"^(- |\d+\. )", lines[i]):
                items.append(_re.sub(r"^(- |\d+\. )", "", lines[i]).strip())
                i += 1
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{_inline(x)}</li>" for x in items) + f"</{tag}>")
        else:
            para = [ln.strip()]
            i += 1
            while i < len(lines) and lines[i].strip() and not _re.match(r"^(#{2,3} |- |\d+\. |\|)", lines[i]):
                para.append(lines[i].strip())
                i += 1
            out.append(f"<p>{_inline(' '.join(para))}</p>")
    return "\n".join(out), toc


def load_md(folder):
    items = []
    for f in sorted((CONTENT / folder).glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        _, front, body = raw.split("---", 2)
        meta, faqs = {}, []
        for line in front.strip().split("\n"):
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k == "faq":
                q, _, a = v.partition("|")
                faqs.append((tokens(q.strip()), tokens(a.strip())))
            else:
                meta[k] = v
        meta["faq"] = faqs
        meta["related"] = [x.strip() for x in meta.get("related", "").split(",") if x.strip()]
        meta["order"] = int(meta.get("order", 99))
        meta["html"], meta["toc"] = md(body)
        words = len(_re.sub(r"<[^>]+>", " ", meta["html"]).split())
        meta["minutes"] = max(2, round(words / 200))
        meta["words"] = words
        items.append(meta)
    return sorted(items, key=lambda x: x["order"])


ARTICLES = load_md("kennisbank")
LANDINGS = load_md("paginas")


def nl_date(iso):
    maanden = ["januari", "februari", "maart", "april", "mei", "juni", "juli", "augustus", "september", "oktober", "november", "december"]
    y, m, d = iso.split("-")
    return f"{int(d)} {maanden[int(m) - 1]} {y}"


def related_rows(ids):
    items = [BY_ID[i] for i in ids if i in BY_ID]
    return treatment_rows(items) if items else ""


def article_cards(items, heading="h3"):
    cards = []
    for a in items:
        cards.append(f"""<li class="card">
  <a class="card-link" href="/massagegids/{a['slug']}">
    <span class="card-media">{picture(a['image'], a.get('imageAlt', ''), sizes="(min-width: 900px) 30vw, (min-width: 600px) 45vw, 100vw")}</span>
    <div class="card-body">
      <{heading} class="card-title">{E(a['h1'])}</{heading}>
      <p class="card-text">{E(a['lead'])}</p>
      <p class="card-meta">{a['minutes']} min lezen</p>
    </div>
  </a>
</li>""")
    return f'<ul class="card-grid">{"".join(cards)}</ul>'


def article_schema(a, path):
    return {
        "@type": "BlogPosting",
        "@id": f"{DOMAIN}{path}#article",
        "headline": a["h1"],
        "description": a["description"],
        "image": f"{DOMAIN}/assets/images/{a['image']}.webp",
        "datePublished": a.get("date", TODAY),
        "dateModified": a.get("updated", a.get("date", TODAY)),
        "inLanguage": "nl-NL",
        "wordCount": a["words"],
        "author": {"@type": "Organization", "name": SITE["name"], "url": DOMAIN + "/"},
        "publisher": {"@id": BIZ_ID},
        "mainEntityOfPage": {"@id": f"{DOMAIN}{path}#webpage"},
        "isPartOf": {"@id": f"{DOMAIN}/massagegids#webpage"},
    }


def page_article(a):
    path = f"/massagegids/{a['slug']}"
    crumbs = [("Home", "/"), ("Massagegids", "/massagegids"), (a["h1"], path)]
    schema = [business_schema(), website_schema(), webpage_schema(path, a["title"], a["description"]), article_schema(a, path), crumb_schema(crumbs)]
    if a["faq"]:
        schema.append(faq_schema(a["faq"]))
    toc = "".join(f'<li><a href="#{an}">{E(ti)}</a></li>' for an, ti in a["toc"])
    others = [x for x in ARTICLES if x["slug"] != a["slug"]][:3]
    faq_html = f"""<section class="section section-tint" aria-labelledby="faq-title">
    <div class="wrap faq-grid">
      <div><h2 id="faq-title">Vragen over dit onderwerp</h2><p>Meer antwoorden vind je bij de <a href="/veelgestelde-vragen">veelgestelde vragen</a>.</p></div>
      {faq_block(a['faq'])}
    </div>
  </section>""" if a["faq"] else ""
    return f"""{head(a['title'], a['description'], path, schema=schema, preload_img=a['image'], preload_sizes="(min-width: 1000px) 1040px, 100vw")}
<body>
{header('/massagegids')}
<main id="main">
  <article>
    <header class="article-hero">
      <div class="wrap wrap-narrow">
        {breadcrumbs(crumbs)}
        <h1 id="page-title">{E(a['h1'])}</h1>
        <p class="page-lead">{E(a['lead'])}</p>
        <p class="article-meta"><span>Door {SITE['name']}</span><time datetime="{a.get('updated', a.get('date'))}">{nl_date(a.get('updated', a.get('date')))}</time><span>{a['minutes']} min lezen</span></p>
      </div>
      <figure class="wrap wrap-medium article-media">{picture(a['image'], a.get('imageAlt', ''), eager=True, sizes="(min-width: 1000px) 1040px, 100vw")}</figure>
    </header>
    <div class="wrap article-layout">
      <aside class="toc" aria-label="Inhoud van dit artikel">
        <p class="toc-title">In dit artikel</p>
        <ol>{toc}</ol>
      </aside>
      <div class="prose article-body">{a['html']}</div>
    </div>
  </article>
  <section class="section" aria-labelledby="rel-title">
    <div class="wrap">
      <div class="section-head"><h2 id="rel-title">Passende behandelingen</h2><p><a class="link" href="/massages">Alle behandelingen {icon('arrow')}</a></p></div>
      {related_rows(a['related'])}
    </div>
  </section>
  {faq_html}
  <section class="section" aria-labelledby="more-title">
    <div class="wrap">
      <div class="section-head"><h2 id="more-title">Verder lezen</h2><p><a class="link" href="/massagegids">Naar de massagegids {icon('arrow')}</a></p></div>
      {article_cards(others)}
    </div>
  </section>
  {cta_band()}
</main>
{footer()}"""


def page_kennisbank():
    path = "/massagegids"
    title = "Massagegids: uitleg en tips | Baitan Thai Massage Capelle"
    desc = "Alles over Thaise massage, sportmassage, hot stone en aromatherapie. Uitleg, tips voor je eerste massage en hulp bij het kiezen van de juiste behandeling."
    crumbs = [("Home", "/"), ("Massagegids", path)]
    itemlist = {"@type": "ItemList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "url": f"{DOMAIN}/massagegids/{a['slug']}", "name": a["h1"]} for i, a in enumerate(ARTICLES)]}
    schema = [business_schema(), website_schema(), webpage_schema(path, title, desc, "CollectionPage"), crumb_schema(crumbs), itemlist]
    return f"""{head(title, desc, path, schema=schema)}
<body>
{header(path)}
<main id="main">
  <section class="page-hero page-hero-plain" aria-labelledby="page-title">
    <div class="wrap">
      {breadcrumbs(crumbs)}
      <h1 id="page-title">Massagegids</h1>
      <p class="page-lead">Uitleg over massagevormen, tips voor je eerste bezoek en hulp bij het kiezen van de behandeling die bij je past.</p>
    </div>
  </section>
  <section class="section section-flush-top" aria-label="Artikelen">
    <div class="wrap">{article_cards(ARTICLES, 'h2')}</div>
  </section>
  {cta_band()}
</main>
{footer()}"""


def page_landing(p):
    path = f"/{p['slug']}"
    crumbs = [("Home", "/"), (p["h1"] if p.get("kind") == "basis" else p["h1"].replace(" in Capelle aan den IJssel", ""), path)]
    page_type = "AboutPage" if p["slug"] == "over-baitan" else "WebPage"
    schema = [business_schema(), website_schema(), webpage_schema(path, p["title"], p["description"], page_type), crumb_schema(crumbs)]
    if p["faq"]:
        schema.append(faq_schema(p["faq"]))
    faq_html = f"""<section class="section section-tint" aria-labelledby="faq-title">
    <div class="wrap faq-grid">
      <div><h2 id="faq-title">Veelgestelde vragen</h2><p>Staat je vraag er niet bij? Bekijk <a href="/veelgestelde-vragen">alle vragen</a> of bel <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a>.</p></div>
      {faq_block(p['faq'])}
    </div>
  </section>""" if p["faq"] else ""
    extra_btn = (f'<a class="btn btn-outline" {ext(SITE["whatsapp_gift_url"])}>{WHATSAPP} Cadeaubon via WhatsApp</a>' if p["slug"] == "cadeaubon"
                 else '<a class="btn btn-outline" href="/prijzen">Prijzen bekijken</a>')
    rel = related_rows(p["related"])
    return f"""{head(p['title'], p['description'], path, schema=schema, preload_img=p['image'], preload_sizes="(min-width: 900px) 42vw, 100vw")}
<body>
{header(path)}
<main id="main">
  <section class="page-hero" aria-labelledby="page-title">
    <div class="wrap page-hero-grid">
      <div>
        {breadcrumbs(crumbs)}
        <h1 id="page-title">{E(p['h1'])}</h1>
        <p class="page-lead">{E(p['lead'])}</p>
        <div class="btn-row">
          <a class="btn btn-primary" {ext(SITE['booking_url'])}>Afspraak maken {icon('arrow')}</a>
          {extra_btn}
        </div>
      </div>
      <figure class="page-hero-media">{picture(p['image'], p.get('imageAlt', ''), eager=True, sizes="(min-width: 900px) 42vw, 100vw")}</figure>
    </div>
  </section>
  <section class="section">
    <div class="wrap detail-grid">
      <div class="prose">{p['html']}</div>
      {side_card(gift=p['slug'] == 'cadeaubon')}
    </div>
  </section>
  {f'<section class="section section-flush-top" aria-labelledby="rel-title"><div class="wrap"><div class="section-head"><h2 id="rel-title">Behandelingen</h2><p><a class="link" href="/massages">Alle behandelingen {icon("arrow")}</a></p></div>{rel}</div></section>' if rel else ''}
  {faq_html}
  {cta_band(*DUO_CTA) if p['slug'] == 'massage-voor-stellen' else cta_band()}
</main>
{footer()}"""


def page_faq():
    path = "/veelgestelde-vragen"
    title = "Veelgestelde vragen over massage | Baitan Thai Massage"
    desc = "Antwoorden op veelgestelde vragen over Baitan: prijzen, annuleren, betalen, parkeren, cadeaubonnen en wat je kunt verwachten van je massage."
    crumbs = [("Home", "/"), ("Veelgestelde vragen", path)]
    groups = [
        ("Afspraak en bezoek", list(FAQ)),
        ("Prijzen", [price_faq(t) for t in TREATMENTS if t["solo"] or t["id"] == "duo"]),
        ("Cadeaubon en spaarkaart", next((p["faq"] for p in LANDINGS if p["slug"] == "cadeaubon"), [])),
        ("Over de behandelingen", [q for a in ARTICLES for q in a["faq"]][:8]),
    ]
    seen, allq = set(), []
    for _, qs in groups:
        for q in qs:
            if q[0] not in seen:
                seen.add(q[0])
                allq.append(q)
    schema = [business_schema(), website_schema(), webpage_schema(path, title, desc, "FAQPage") | {"mainEntity": faq_schema(allq)["mainEntity"]}, crumb_schema(crumbs)]
    seen2, blocks = set(), []
    for name, qs in groups:
        qs = [q for q in qs if q[0] not in seen2]
        seen2.update(q[0] for q in qs)
        if qs:
            anchor = _re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
            blocks.append(f'<section class="faq-group" aria-labelledby="{anchor}"><h2 id="{anchor}">{name}</h2>{faq_block(qs)}</section>')
    nav = "".join(f'<li><a href="#{_re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-")}">{n}</a></li>' for n, qs in groups if qs)
    return f"""{head(title, desc, path, schema=schema)}
<body>
{header()}
<main id="main">
  <section class="page-hero page-hero-plain" aria-labelledby="page-title">
    <div class="wrap">
      {breadcrumbs(crumbs)}
      <h1 id="page-title">Veelgestelde vragen</h1>
      <p class="page-lead">Alles over afspraken, prijzen, cadeaubonnen en de behandelingen. Staat je vraag er niet bij? Bel <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a> of stuur een <a {ext(SITE['whatsapp_question_url'])}>WhatsApp-bericht</a>.</p>
    </div>
  </section>
  <section class="section section-flush-top">
    <div class="wrap faq-page">
      <nav class="toc" aria-label="Onderwerpen"><p class="toc-title">Onderwerpen</p><ol>{nav}</ol></nav>
      <div class="faq-groups">{"".join(blocks)}</div>
    </div>
  </section>
  {cta_band()}
</main>
{footer()}"""


# ---------------------------------------------------------------- write
def write(name, content):
    p = OUT / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)

    pages = {"index.html": page_home(), "massages.html": page_massages(), "prijzen.html": page_prijzen(), "contact.html": page_contact(),
             "voorwaarden.html": page_legal("voorwaarden"), "privacy.html": page_legal("privacy"), "404.html": page_404()}
    for t in PAGES:
        pages[f'{t["slug"]}.html'] = page_treatment(t)
    pages["massagegids/index.html"] = page_kennisbank()
    for a in ARTICLES:
        pages[f"massagegids/{a['slug']}.html"] = page_article(a)
    for lp in LANDINGS:
        pages[f"{lp['slug']}.html"] = page_landing(lp)
    pages["veelgestelde-vragen.html"] = page_faq()
    for name, content in pages.items():
        write(name, content)

    hero_img = Path(HERO.get("image", "thaise-massage-capelle-aan-den-ijssel")).stem
    urls = [("/", "1.0", hero_img), ("/massages", "0.9", None), ("/prijzen", "0.9", None)] + [(f'/{t["slug"]}', "0.8", t["image"]) for t in PAGES] + [("/contact", "0.8", None)] \
        + [(f"/{lp['slug']}", "0.7", lp["image"]) for lp in LANDINGS] + [("/veelgestelde-vragen", "0.6", None), ("/massagegids", "0.6", None)] \
        + [(f"/massagegids/{a['slug']}", "0.6", a["image"]) for a in ARTICLES]
    sm = "".join(
        f"<url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority>"
        + (f"<image:image><image:loc>{DOMAIN}/assets/images/{img}.webp</image:loc></image:image>" if img else "")
        + "</url>"
        for u, p, img in urls
    )
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">{sm}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n")
    write("site.webmanifest", json.dumps({
        "name": SITE["name"], "short_name": "Baitan", "start_url": "/", "display": "browser",
        "background_color": "#f8f4ec", "theme_color": "#2f3829",
        "icons": [{"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"}, {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }, ensure_ascii=False, indent=2))

    print(f"Gebouwd: {len(pages)} pagina's in {OUT}")


if __name__ == "__main__":
    main()
