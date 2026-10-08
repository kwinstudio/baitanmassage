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
        "image": Path(_t.get("image", "/assets/images/baitan-hero-atmospheric.webp")).stem,
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

QUIZ = [
    ("Waar heb je vandaag vooral behoefte aan?", [("Ontspannen", "aroma"), ("Traditionele technieken", "thai"), ("Steviger, gericht op spieren", "sport"), ("Samen ontspannen", "duo")]),
    ("Wat spreekt je het meest aan?", [("Warme olie", "thai"), ("Een geur naar keuze", "aroma"), ("Warme stenen", "hotstone"), ("Geen voorkeur", "neutral")]),
    ("Hoe wil je de massage ervaren?", [("Rustig en comfortabel", "aroma"), ("Traditioneel", "thai"), ("Steviger", "sport"), ("Samen", "duo")]),
    ("Welke setting past het best?", [("Alleen", "neutral"), ("Samen met iemand", "duo"), ("Met warme stenen", "hotstone"), ("Met olie", "aroma")]),
    ("Waar neig je nu het meest naar?", [("Thaise massage", "thai"), ("Aromatherapie", "aroma"), ("Sportmassage", "sport"), ("Hot stone", "hotstone")]),
]

TODAY = datetime.date.today().isoformat()
VERSION = TODAY.replace("-", "")

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
def head(title, description, path, og_image="og-image.jpg", schema=None, robots="index,follow,max-image-preview:large"):
    canonical = DOMAIN + path
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
<meta property="og:image:alt" content="Baitan Thai Massage in Capelle aan den IJssel">
<meta name="twitter:card" content="summary_large_image">
<link rel="alternate" hreflang="nl-NL" href="{canonical}">
{f'<meta name="google-site-verification" content="{E(SITE["google_verification"])}">' if SITE["google_verification"] else ""}
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/fonts/newsreader.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/figtree.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/styles.css?v={VERSION}">
{ld}
</head>"""


NAV = [("/massages", "Behandelingen"), ("/prijzen", "Prijzen"), ("/#massagekeuze", "Massagekeuze"), ("/#reviews", "Reviews"), ("/contact", "Contact")]


def header(current=""):
    cur = ' aria-current="page"'
    links = "".join(
        f'<li><a class="nav-link" href="{href}"{cur if href == current else ""}>{label}</a></li>' for href, label in NAV
    )
    return f"""<a class="skip-link" href="#main">Naar de inhoud</a>
<header class="site-header" data-header>
  <div class="wrap header-inner">
    <a class="brand" href="/" aria-label="Baitan Thai Massage, naar de homepage">
      <span class="brand-mark" aria-hidden="true"><span>B</span></span>
      <span class="brand-text">Baitan<small>Thai Massage</small></span>
    </a>
    <nav class="site-nav" aria-label="Hoofdmenu">
      <ul class="nav-list" id="nav-list">{links}</ul>
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
        <a class="brand brand-light" href="/"><span class="brand-mark" aria-hidden="true"><span>B</span></span><span class="brand-text">Baitan<small>Thai Massage</small></span></a>
        <p>{E(SITE['tagline'])}</p>
        <a class="btn btn-light btn-sm" {ext(SITE['booking_url'])}>Afspraak maken</a>
      </div>
      <div>
        <h2 class="footer-title">Behandelingen</h2>
        <ul class="footer-list">{treat}<li><a href="/prijzen">Alle prijzen</a></li></ul>
      </div>
      <div>
        <h2 class="footer-title">Contact</h2>
        <address class="footer-list">
          <span>{SITE['street']}</span><span>{SITE['postal']} {SITE['city']}</span>
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
      <span>© {datetime.date.today().year} {SITE['name']} · KVK {SITE['kvk']} · BTW {SITE['btw']}</span>
      <span class="footer-legal"><a href="/voorwaarden">Huisregels &amp; voorwaarden</a><a href="/privacy">Privacy &amp; cookies</a></span>
    </div>
    <p class="footer-note">De foto's op deze website zijn sfeerbeelden.</p>
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
<script src="/app.js?v={VERSION}" defer></script>
</body>
</html>"""


def picture(name, alt, cls="", eager=False, sizes=None):
    w, h = img_size(name)
    load = 'fetchpriority="high"' if eager else 'loading="lazy"'
    return f'<img class="{cls}" src="/assets/images/{name}.webp" alt="{E(alt)}" width="{w}" height="{h}" {load} decoding="async">'


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
        body.append(f'<tr><th scope="row">{t["name"]} duo</th>{cells}</tr>')
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
    <span class="treatment-media">{picture(t['image'], t['alt'])}</span>
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


def hours_short():
    def h(x):
        return x.split(":")[0].lstrip("0") if x.endswith(":00") else x
    a, b = HOURS
    return f"Ma–vr {h(a['opens'])}–{h(a['closes'])} uur · za–zo {h(b['opens'])}–{h(b['closes'])} uur"


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


def cta_band(title="Zin in een moment voor jezelf?", text="Kies in de online agenda een behandeling en een tijd die jou uitkomt."):
    return f"""<section class="cta-band">
  <div class="wrap cta-inner">
    <div>
      <h2>{title}</h2>
      <p>{text}</p>
    </div>
    <div class="cta-actions">
      <a class="btn btn-light" {ext(SITE['booking_url'])}>Bekijk vrije tijden {icon('arrow')}</a>
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
      <li>{icon('clock')}<span><strong>Openingstijden</strong>{hours_table()}</span></li>
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
      <p>De kaart van Google Maps laden we pas als je daarvoor kiest.</p>
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
        "logo": f"{DOMAIN}/apple-touch-icon.png",
        "image": [f"{DOMAIN}/og-image.jpg", f"{DOMAIN}/assets/images/baitan-hero-atmospheric.webp"],
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
    schema = [business_schema(), website_schema(), webpage_schema("/", title, desc), faq_schema(FAQ)]
    quiz = []
    for qi, (q, opts) in enumerate(QUIZ):
        buttons = "".join(f'<button type="button" class="quiz-option" data-score="{s}">{E(label)}</button>' for label, s in opts)
        quiz.append(f'<fieldset class="quiz-step" data-step="{qi}"{"" if qi == 0 else " hidden"}><legend>{E(q)}</legend><div class="quiz-options">{buttons}</div></fieldset>')
    quiz_data = {t["id"]: {"name": t["name"], "text": t["short"], "url": f'/{t["slug"]}' if t["page"] else "/prijzen"} for t in TREATMENTS}
    gift_btn = f'<a class="btn btn-outline btn-sm" {ext(SITE["whatsapp_gift_url"])}>{WHATSAPP} Vraag via WhatsApp</a>'
    body = f"""{head(title, desc, "/", schema=schema)}
<body class="page-home">
{header()}
<main id="main">
  <section class="hero" aria-labelledby="hero-title">
    <div class="hero-media">{picture(Path(HERO.get('image', 'baitan-hero-atmospheric')).stem, HERO.get('imageAlt', ''), 'hero-img', eager=True)}</div>
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
        <li>{icon('clock')}<span>{hours_short()}</span></li>
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
        <p>Beantwoord vijf korte vragen. Daarna zie je meteen welke behandeling het best aansluit bij je wensen.</p>
      </div>
      <div class="quiz" data-quiz='{E(json.dumps(quiz_data, ensure_ascii=False))}'>
        <div class="quiz-progress"><span data-quiz-label>Vraag 1 van 5</span><span class="quiz-track"><span data-quiz-bar></span></span></div>
        {"".join(quiz)}
        <div class="quiz-result" data-quiz-result hidden tabindex="-1">
          <p class="quiz-result-label">Jouw beste match</p>
          <h3 data-quiz-title></h3>
          <p data-quiz-text></p>
          <div class="btn-row">
            <a class="btn btn-primary" {ext(SITE['booking_url'])}>Afspraak maken</a>
            <a class="btn btn-outline" href="/massages" data-quiz-link>Bekijk behandeling</a>
          </div>
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
      <figure class="about-media">{picture(Path(ABOUT.get('image', 'thai-herbal-compress')).stem, ABOUT.get('imageAlt', ''))}</figure>
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
        <p>Op basis van {SITE['review_count']} Google-reviews van gasten. Lees wat zij zeggen, of laat zelf een review achter na je bezoek.</p>
        <div class="btn-row">
          <a class="btn btn-light" {ext(SITE['maps_url'])}>Lees de reviews</a>
          <a class="btn btn-ghost-light" {ext(SITE['review_write_url'])}>Schrijf een review</a>
        </div>
      </div>
    </div>
  </section>

  <section class="section" id="faq" aria-labelledby="faq-title">
    <div class="wrap faq-grid">
      <div>
        <h2 id="faq-title">Veelgestelde vragen</h2>
        <p>Staat je vraag er niet bij? Bel <a href="tel:{SITE['phone_href']}">{SITE['phone_display']}</a> of stuur een <a {ext(SITE['whatsapp_question_url'])}>WhatsApp-bericht</a>.</p>
      </div>
      {faq_block(FAQ)}
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


def page_treatment(t):
    path = f'/{t["slug"]}'
    crumbs = [("Home", "/"), ("Behandelingen", "/massages"), (t["name"], path)]
    others = [o for o in TREATMENTS if o["id"] != t["id"]]
    is_duo = t["id"] == "duo"
    prices_html = duo_table() if is_duo else price_table([t], caption=f'Prijzen {t["name"]}', link=False)
    price_note = "Prijs voor twee personen samen." if is_duo else "Prijs per persoon. Onder elke prijs staat de prijs voor twee personen samen (duo)."
    faq_items = [FAQ[0], FAQ[1], FAQ[4], FAQ[2]]
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
    return f"""{head(t['seo_title'], t['seo_description'], path, schema=schema)}
<body>
{header('/massages')}
<main id="main">
  <section class="page-hero" aria-labelledby="page-title">
    <div class="wrap page-hero-grid">
      <div>
        {breadcrumbs(crumbs)}
        <h1 id="page-title">{t['h1']}</h1>
        <p class="page-lead">{t['lead']}</p>
        <div class="btn-row">
          <a class="btn btn-primary" {ext(SITE['booking_url'])}>Afspraak maken {icon('arrow')}</a>
          <a class="btn btn-outline" href="#prijs">Prijzen bekijken</a>
        </div>
      </div>
      <figure class="page-hero-media">{picture(t['image'], t['alt'], eager=True)}</figure>
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
        <a class="btn btn-primary btn-block" {ext(SITE['booking_url'])}>Kies een tijd</a>
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
  {cta_band()}
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
    schema = [business_schema(), website_schema(), webpage_schema(path, title, desc), crumb_schema(crumbs)]
    notes = [
        ("Duo-massage", "Met z'n tweeën tegelijk een massage. De duo-prijs geldt voor twee personen samen."),
        ("Betalen", "Met pin of contant in de salon."),
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
        <a class="btn btn-primary" {ext(SITE['booking_url'])}>Bekijk vrije tijden {icon('arrow')}</a>
      </div>
    </div>
  </section>
  {cta_band()}
</main>
{footer()}"""


def page_contact():
    path = "/contact"
    title = "Contact en route | Baitan Thai Massage Capelle aan den IJssel"
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


def page_legal(kind):
    if kind == "voorwaarden":
        path, title, h1 = "/voorwaarden", "Huisregels en voorwaarden | Baitan Thai Massage", "Huisregels en voorwaarden"
        desc = "Huisregels en algemene voorwaarden van Baitan Thai Massage: reserveren, annuleren, te laat komen, gezondheid en cadeaubonnen."
        sections = [
            ("Algemeen", ["Deze voorwaarden gelden voor diensten, boekingen en overeenkomsten van Baitan Thai Massage. Door een afspraak te maken ga je akkoord met deze voorwaarden."]),
            ("Diensten", ["Baitan biedt ontspannings- en wellnessmassages. De behandelingen zijn niet medisch van aard en vervangen geen behandeling door een arts of specialist."]),
            ("Reservering en betaling", ["Afspraken kunnen online worden geboekt. Volgens de gepubliceerde voorwaarden van Baitan geschiedt betaling vooraf online, tenzij anders overeengekomen. Een afspraak is definitief na ontvangst van de betaling."]),
            ("Annuleren en verzetten", None),
            ("Te laat komen", ["Bij te laat komen kan de behandeltijd worden ingekort. De volledige kosten van de geboekte behandeling blijven verschuldigd."]),
            ("Gezondheid", ["Meld relevante gezondheidsinformatie, waaronder blessures, zwangerschap of medicijngebruik, vóór de behandeling. Baitan kan een behandeling weigeren wanneer gezondheidsrisico's worden ingeschat."]),
            ("Gedrag en hygiëne", ["Respectvol en hygiënisch gedrag is verplicht. Ongepast gedrag kan leiden tot onmiddellijke beëindiging van de behandeling zonder restitutie. Erotische of seksuele verzoeken zijn niet toegestaan."]),
            ("Aansprakelijkheid", ["Baitan is niet aansprakelijk voor verlies, diefstal of schade aan persoonlijke eigendommen. Aansprakelijkheid voor directe schade is beperkt zoals in de officiële voorwaarden is beschreven."]),
            ("Cadeaubonnen", ["Cadeaubonnen zijn niet inwisselbaar voor contant geld en hebben een geldigheidsduur van 12 maanden, tenzij anders vermeld."]),
            ("Overmacht", ["Bij ziekte, storingen of andere onvoorziene omstandigheden kan Baitan een afspraak verzetten of annuleren. In dat geval wordt een nieuwe afspraak of restitutie aangeboden volgens de geldende voorwaarden."]),
            ("Toepasselijk recht", ["Op de dienstverlening is Nederlands recht van toepassing."]),
        ]
        cancel = "<ul><li>Kosteloos annuleren tot 24 uur vóór de afspraak.</li><li>Binnen 24 uur vindt geen restitutie plaats.</li><li>Een afspraak kan één keer kosteloos worden verzet.</li><li>Bij een no-show vervalt de afspraak zonder terugbetaling.</li></ul>"
    else:
        path, title, h1 = "/privacy", "Privacy en cookies | Baitan Thai Massage", "Privacy en cookies"
        desc = "Hoe Baitan Thai Massage omgaat met je gegevens: contact, online boeken via Salonized, Google Maps en cookies."
        sections = [
            ("Contactgegevens", ["Als je Baitan belt, mailt of een WhatsApp-bericht stuurt, gebruiken we alleen de gegevens die nodig zijn om je vraag of afspraak af te handelen."]),
            ("Online boeken via Salonized", ["Voor online reserveringen verwijst deze website naar de officiële Salonized-agenda van Baitan. Als je daar boekt, verwerkt Salonized je gegevens volgens het eigen privacy- en cookiebeleid."]),
            ("Google Maps", ["De kaart van Google Maps wordt pas geladen nadat je op ‘Kaart laden’ klikt. Daarna kan Google technische gegevens verwerken volgens het eigen privacy- en cookiebeleid."]),
            ("Cookies", ["Deze website plaatst geen marketing- of analyticscookies. Lettertypes worden vanaf onze eigen server geladen, niet via Google. Externe diensten zoals Salonized, WhatsApp en Google Maps gebruiken pas cookies als je ze zelf opent."]),
            ("Je rechten", [f"Heb je een vraag over je gegevens of wil je ze laten inzien of verwijderen? Neem contact op via <a href=\"mailto:{SITE['email']}\">{SITE['email']}</a> of <a href=\"tel:{SITE['phone_href']}\">{SITE['phone_display']}</a>."]),
        ]
        cancel = ""
    crumbs = [("Home", "/"), (h1, path)]
    schema = [website_schema(), webpage_schema(path, title, desc), crumb_schema(crumbs)]
    robots = "noindex,follow"
    secs = []
    for h, ps in sections:
        inner = cancel if ps is None else "".join(f"<p>{p}</p>" for p in ps)
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
      <p class="page-lead">Laatst bijgewerkt op {datetime.date.today().strftime('%d-%m-%Y')}.</p>
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
    for name, content in pages.items():
        write(name, content)

    hero_img = Path(HERO.get("image", "baitan-hero-atmospheric")).stem
    urls = [("/", "1.0", hero_img), ("/massages", "0.9", None), ("/prijzen", "0.9", None)] + [(f'/{t["slug"]}', "0.8", t["image"]) for t in PAGES] + [("/contact", "0.8", None)]
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
