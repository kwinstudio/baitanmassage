# Baitan Thai Massage — Pages CMS → GitHub main → Vercel

Deze repository is voorbereid op dezelfde beheerflow als Thai Massage Gouda.

## Workflow

1. De eigenaar past teksten, foto's, openingstijden of prijzen aan in **Pages CMS**.
2. Pages CMS schrijft de wijziging als commit naar **GitHub `main`**.
3. Vercel ziet de nieuwe commit en start automatisch een deployment.
4. `build.py` leest `data/site.json` en `data/treatments.json` en genereert de website in `dist/`.
5. Vercel publiceert `dist/`.

## Bestanden die de klant via Pages CMS beheert

- `data/site.json` — algemene gegevens, homepage, reviews, FAQ, openingstijden, SEO en contact.
- `data/treatments.json` — behandelingen, tijdsduren en prijzen.
- `assets/images/` — nieuwe websitefoto's.
- `.pages.yml` — bepaalt welke velden Pages CMS toont.

Media-instellingen zijn bewust hetzelfde als bij Thai Massage Gouda:

- uploadmap: `assets/images`
- websitepad: `/assets/images`

## Vercel

`vercel.json` bevat al:

- build command: `python3 build.py`
- output directory: `dist`
- clean URLs

Na het importeren van de GitHub-repository in Vercel is normaal gesproken geen handmatige buildconfiguratie meer nodig.

## Pages CMS

Koppel in Pages CMS de Baitan-repository en gebruik branch `main`. De `.pages.yml` in de root wordt automatisch gebruikt.

De klant kan daarna o.a. aanpassen:

- hero-tekst en foto;
- contactgegevens;
- openingstijden;
- massages;
- tijdsduren;
- prijzen;
- Google-reviewscore/aantal;
- FAQ;
- cadeaubon en spaarkaart;
- SEO-titel en omschrijving.

## Eigen reserveringssysteem

De website gebruikt **geen Treatwell voor reserveringen**.

De browser stuurt reserveringen naar de eigen API via:

- `/api/...` wanneer `booking.apiBase` leeg is;
- een aparte backend-URL wanneer `booking.apiBase` in Pages CMS is ingevuld.

De huidige `server.py` bevat de eigen reserveringslogica en SQLite-opslag voor een server met permanente schijfruimte.

### Belangrijk bij Vercel

Gebruik SQLite **niet** als productiedatabase in Vercel Functions. De lokale filesystem-opslag van serverless deployments is niet bedoeld als blijvende afspraken-database.

Voor productie zijn er twee veilige opties:

1. website op Vercel + `server.py` op een aparte server met permanente opslag; of
2. de booking API migreren naar serverless functions met een persistente database zoals PostgreSQL.

Wanneer de bookingbackend apart draait:

- zet `booking.apiBase` in Pages CMS op de HTTPS-URL van de backend;
- zet op de backend `BAITAN_SITE_ORIGIN` op het definitieve websitedomein;
- stel `BAITAN_ADMIN_PASSWORD` server-side in.

Geheimen horen nooit in `data/site.json`, JavaScript of `.pages.yml`.

## Lokaal testen

Website bouwen:

```bash
python3 build.py
```

Website + eigen boekingsbackend starten:

```bash
BAITAN_ADMIN_PASSWORD='kies-een-sterk-wachtwoord' python3 server.py
```

Daarna draait de site standaard op `http://127.0.0.1:8080`.

## GitHub repository

Aanbevolen repositorynaam:

`kwinstudio/baitanmassage`

Zodra die repository bestaat, moeten alle bestanden uit deze map in de root van branch `main` staan.
