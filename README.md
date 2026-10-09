# Baitan Thai Massage: Pages CMS → GitHub `main` → Vercel

Statische website voor Baitan Thai Massage in Capelle aan den IJssel. Er is geen framework en er zijn geen afhankelijkheden: alleen Python 3.

## Workflow

1. De eigenaar past teksten, foto's, openingstijden of prijzen aan in **Pages CMS**.
2. Pages CMS schrijft de wijziging als commit naar **GitHub `main`**.
3. Vercel bouwt automatisch: `python3 build.py` genereert de site in `dist/`.

## Wat staat waar

| Bestand | Inhoud |
|---|---|
| `data/site.json` | Bedrijfsgegevens, homepage, reviews, FAQ, openingstijden, SEO (via Pages CMS) |
| `data/treatments.json` | Behandelingen, teksten, duur, prijs per persoon en duo-prijs (via Pages CMS) |
| `assets/images/` | Foto's (upload via Pages CMS) |
| `content/kennisbank/*.md` (op /massagegids), `content/paginas/*.md` | Artikelen en losse pagina's in Markdown (zie `content/README.md`) |
| `build.py` | Templates, structured data, sitemap en robots.txt |
| `static/styles.css` | Vormgeving (Newsreader + Figtree, zelf gehost in `static/fonts/`) |
| `static/app.js` | Menu, massagekeuze, kaart pas laden na klik, contactbalk |
| `tools/optimize_images.py` | Maakt AVIF/WebP-varianten in `assets/images/r/` voor scherpe, snelle foto's (lokaal draaien na nieuwe foto's) |
| `vercel.json` | Build, redirects van de oude WordPress-URL's, beveiligingsheaders |

## Lokaal testen

    python3 build.py
    cd dist && python3 -m http.server 8000

Clean URLs (`/prijzen` in plaats van `/prijzen.html`) werken alleen op Vercel of met `npx serve dist`.

## SEO

- Elke behandeling heeft een eigen pagina met een unieke titel, meta-description, BreadcrumbList, Service- en FAQPage-schema.
- Op de homepage staat het `HealthAndBeautyBusiness`-schema met adres, openingstijden en alle prijzen.
- Canonical-URL's wijzen naar `seo.canonical` (https://baitanmassage.nl). Op `*.vercel.app` stuurt Vercel `X-Robots-Tag: noindex`, zodat Google alleen het echte domein indexeert.
- Oude WordPress-URL's (`/tarieven`, `/contact/`, `/online-reserveren`, `/privacy-policy`, `/algemene-voorwaarden`) krijgen een 301-redirect.
- Na het verhuizen van baitanmassage.nl naar Vercel: dien `https://baitanmassage.nl/sitemap.xml` in bij Google Search Console.

## Boeken

Alle "Afspraak maken"-knoppen gaan naar de Salonized-agenda (`booking.salonizedBookingUrl`). Er is geen eigen reserveringssysteem meer op de site.

## Foto's

De foto's zijn opgeschaald met Real-ESRGAN (2x, met ruisonderdrukking) en staan als master in `assets/images/`.
Na het toevoegen of vervangen van een foto: `python3 tools/optimize_images.py` (vereist Pillow met AVIF), dan committen.
Zonder varianten valt de site automatisch terug op het originele bestand.
