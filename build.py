#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"

def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)

def money(value) -> str:
    value = float(value)
    return f"€{int(value)}" if value.is_integer() else f"€{value:.2f}".replace(".", ",")

def load_json(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))

def active_treatments(treatments):
    return [t for t in treatments if t.get("active", True)]

def hero(site):
    h = site["hero"]
    return f'''<section class="hero" id="home"><div class="hero-copy"><span class="eyebrow">{esc(h.get('eyebrow'))}</span><h1>{esc(h.get('title'))}</h1><p class="lead">{esc(h.get('text'))}</p><div class="hero-actions"><a class="btn" href="#boeken">{esc(h.get('primaryButton'))}</a><a class="btn btn-outline" href="#massagekeuze">{esc(h.get('secondaryButton'))}</a></div></div><div class="hero-photo"><img src="{esc(h.get('image'))}" alt="{esc(h.get('imageAlt'))}" fetchpriority="high"><span class="photo-badge">{esc(h.get('badge'))}</span></div></section>'''


def trustbar(site):
    o = site["opening"]; r = site["reviews"]; t = site["trust"]
    return f'''<section class="trustbar" aria-label="Praktische informatie"><div class="container trust-grid"><a class="trust-item" href="{esc(r.get('url'))}" target="_blank" rel="noopener"><div class="trust-kicker">Google</div><div class="trust-value">{esc(r.get('rating'))} · {esc(r.get('count'))} reviews</div></a><div class="trust-item"><div class="trust-kicker">Locatie</div><div class="trust-value">{esc(t.get('location'))}</div></div><div class="trust-item"><div class="trust-kicker">Parkeren</div><div class="trust-value">{esc(t.get('parking'))}</div></div><div class="trust-item"><div class="trust-kicker">Ma — vr</div><div class="trust-value">{esc(o.get('weekdayOpen'))} — {esc(o.get('weekdayClose'))}</div></div></div></section>'''

def booking(site, treatments):
    b = site["booking"]
    provider = str(b.get("provider") or "custom").lower()
    treatwell_widget = str(b.get("treatwellWidgetUrl") or "").strip()
    treatwell_link = str(b.get("treatwellBookingUrl") or "").strip()
    image = b.get("image") or site.get("hero",{}).get("image")
    image_alt = b.get("imageAlt") or "Behandelruimte van Baitan Thai Massage"

    if provider == "treatwell" and (treatwell_widget or treatwell_link):
        if treatwell_widget:
            booking_ui = f'''<div class="treatwell-panel"><iframe class="treatwell-widget" src="{esc(treatwell_widget)}" title="Boek een afspraak bij Baitan via Treatwell" loading="lazy" allow="payment *"></iframe></div>'''
        else:
            booking_ui = f'''<div class="treatwell-panel treatwell-link-panel"><div><div class="eyebrow">Treatwell</div><h3>Bekijk beschikbare tijden</h3><p>Boek direct in de actuele agenda van Baitan.</p><a class="btn booking-submit" href="{esc(treatwell_link)}" target="_blank" rel="noopener">Boek via Treatwell <span aria-hidden="true">→</span></a></div></div>'''
        return f'''<section class="section" id="boeken"><div class="container"><div class="section-head"><div><div class="eyebrow">{esc(b.get('kicker'))}</div><h2>{esc(b.get('title'))}</h2></div><p>{esc(b.get('text'))}</p></div><div class="booking-shell treatwell-booking"><div class="booking-copy booking-copy-rich"><figure class="booking-visual"><img src="{esc(image)}" alt="{esc(image_alt)}" loading="lazy"><figcaption>Baitan</figcaption></figure><div class="booking-copy-text"><div class="eyebrow">Online reserveren</div><h3>{esc(b.get('panelTitle'))}</h3><p>Beschikbaarheid en afspraken worden rechtstreeks via Treatwell gesynchroniseerd.</p></div></div>{booking_ui}</div></div></section>'''

    options = ''.join(f'<option value="{esc(t["id"])}">{esc(t["name"])}</option>' for t in active_treatments(treatments))
    return f'''<section class="section" id="boeken"><div class="container"><div class="section-head"><div><div class="eyebrow">{esc(b.get('kicker'))}</div><h2>{esc(b.get('title'))}</h2></div><p>{esc(b.get('text'))}</p></div><div class="booking-shell"><div class="booking-copy"><div class="eyebrow">Reserveren</div><h3 style="font-size:2.4rem;margin-top:12px">{esc(b.get('panelTitle'))}</h3><ol class="booking-steps"><li class="booking-step"><span class="booking-step-num">01</span><span>Behandeling</span></li><li class="booking-step"><span class="booking-step-num">02</span><span>Datum &amp; tijd</span></li><li class="booking-step"><span class="booking-step-num">03</span><span>Bevestigen</span></li></ol></div><div class="booking-panel">
<label class="field-label" for="serviceSelect">Kies je behandeling</label><div class="select-wrap"><select id="serviceSelect"><option value="">Selecteer een massage</option>{options}</select></div>
<div class="duration-wrap"><span class="field-label">Kies je duur</span><div class="duration-grid" id="durationGrid"><p>Kies eerst een behandeling.</p></div></div>
<div class="booking-summary" id="bookingSummary" hidden><span>Behandeling<br><strong id="summaryService"></strong></span><span>Duur &amp; prijs<br><strong id="summaryChoice"></strong></span></div>
<button class="btn booking-submit" id="bookButton" disabled aria-disabled="true">Kies datum en tijd <span aria-hidden="true">→</span></button>
<div class="booking-flow-step" id="bookingStepDate" hidden><div class="booking-divider"></div><label class="field-label" for="bookingDate">Datum</label><input class="booking-input" type="date" id="bookingDate"><span class="field-label slot-label">Beschikbare tijden</span><div class="slots-grid" id="slotsGrid" aria-live="polite"></div></div>
<div class="booking-flow-step" id="bookingStepDetails" hidden><div class="booking-divider"></div><div class="selected-time"><span>Gekozen tijd</span><strong id="selectedTimeText"></strong></div><form id="bookingForm" class="booking-form"><label>Naam<input class="booking-input" name="name" autocomplete="name" required></label><label>E-mailadres<input class="booking-input" name="email" type="email" autocomplete="email" required></label><label>Telefoonnummer<input class="booking-input" name="phone" type="tel" autocomplete="tel" required></label><label>Opmerking <span>(optioneel)</span><textarea class="booking-input" name="notes" rows="3" maxlength="500"></textarea></label><button class="btn booking-submit" type="submit">Bevestig reservering</button></form></div>
<p class="form-error" id="bookingError" hidden role="alert"></p>
<div class="booking-confirmation" id="bookingConfirmation" hidden><div class="confirmation-mark" aria-hidden="true">✓</div><div><div class="eyebrow">Reservering bevestigd</div><h3>Tot snel bij Baitan.</h3><p id="confirmationText"></p></div></div>
</div></div></div></section>'''


def treatments_section(site, treatments):
    cards=[]
    booking_url=str(site.get('booking',{}).get('treatwellBookingUrl') or '#boeken')
    external=' target="_blank" rel="noopener"' if booking_url.startswith('http') else ''
    for t in active_treatments(treatments):
        ds=t.get('durations') or []
        meta=''.join(f'<span>{int(d["minutes"])} min · {money(d["price"])}</span>' for d in ds)
        start=min((float(d['price']) for d in ds), default=0)
        detail='/' + str(t.get('slug') or '').strip('/')
        image=t.get('image') or site.get('hero',{}).get('image')
        label=t.get('imageLabel') or ''
        label_html=f'<span class="media-label">{esc(label)}</span>' if label else ''
        cards.append(f'''<article class="treatment treatment-visual"><a class="treatment-media" href="{esc(detail)}" data-treatment-modal="{esc(t.get('id'))}"><img src="{esc(image)}" alt="{esc(t.get('imageAlt') or t.get('name'))}" loading="lazy" decoding="async">{label_html}</a><div class="treatment-body"><div class="treatment-topline"><h3>{esc(t.get('name'))}</h3><div class="treatment-price">vanaf {money(start)}</div></div><p>{esc(t.get('description'))}</p><div class="treatment-meta">{meta}</div><div class="treatment-actions"><a class="text-link" href="{esc(detail)}" data-treatment-modal="{esc(t.get('id'))}">Bekijk behandeling <span>→</span></a><a class="text-link" href="{esc(booking_url)}"{external}>Afspraak <span>→</span></a></div></div></article>''')
    modal='''<dialog class="site-dialog treatment-dialog" id="treatmentDialog" aria-labelledby="treatmentDialogTitle"><button class="dialog-close" type="button" data-dialog-close aria-label="Sluiten">×</button><div class="treatment-dialog-grid"><div class="dialog-media"><img id="treatmentDialogImage" alt=""><span class="media-label" id="treatmentDialogLabel"></span></div><div class="dialog-content"><div class="eyebrow">Behandeling</div><h2 id="treatmentDialogTitle"></h2><p id="treatmentDialogText"></p><ul class="dialog-features" id="treatmentDialogFeatures"></ul><div class="dialog-prices" id="treatmentDialogPrices"></div><div class="dialog-actions"><a class="btn" id="treatmentDialogBook" href="#boeken">Afspraak maken</a><a class="text-link" id="treatmentDialogPage" href="/massages">Volledige pagina <span>→</span></a></div></div></div></dialog>'''
    return '<section class="section section-soft" id="massages"><div class="container"><div class="section-head"><div><div class="eyebrow">Behandelingen</div><h2>Onze massages</h2></div><a class="btn btn-outline" href="/massages">Alle behandelingen</a></div><div class="treatments visual-treatments">'+''.join(cards)+'</div></div></section>'+modal

def massage_choice_section(site):
    mood=(site.get('gallery') or [{}])[2] if len(site.get('gallery') or [])>2 else {}
    image=mood.get('image') or site.get('hero',{}).get('image')
    label=mood.get('label') or 'Sfeerbeeld'
    questions = [
      ("Waar heb je vandaag vooral behoefte aan?", [("Ontspannen","aroma"),("Traditionele technieken","thai"),("Steviger gericht op spieren","sport"),("Samen ontspannen","duo")]),
      ("Wat spreekt je het meest aan?", [("Warme olie","thai"),("Geur naar keuze","aroma"),("Warme stenen","hotstone"),("Geen voorkeur","neutral")]),
      ("Hoe wil je de massage ervaren?", [("Rustig en comfortabel","aroma"),("Traditioneel","thai"),("Steviger","sport"),("Samen","duo")]),
      ("Welke setting past het best?", [("Alleen","neutral"),("Samen met iemand","duo"),("Met warme stenen","hotstone"),("Met olie","aroma")]),
      ("Waar neig je nu het meest naar?", [("Thaise massage","thai"),("Aromatherapie","aroma"),("Sportmassage","sport"),("Hot stone of duo","hotstone")])
    ]
    blocks=[]
    for i,(question,answers) in enumerate(questions,1):
        opts=''.join(f'<button type="button" class="choice-option" data-score="{esc(score)}">{esc(label)}</button>' for label,score in answers)
        hidden=' hidden' if i>1 else ''
        blocks.append(f'<fieldset class="choice-question" data-question="{i}"{hidden}><legend><span>0{i}</span>{esc(question)}</legend><div class="choice-options">{opts}</div></fieldset>')
    return f'''<section class="section" id="massagekeuze"><div class="container"><div class="section-head"><div><div class="eyebrow">Massagekeuze</div><h2>Welke massage past bij mij?</h2></div><p>Beantwoord vijf korte vragen. De uitkomst is een praktische keuzehulp, geen medische diagnose.</p></div><div class="choice-layout"><figure class="choice-photo"><img src="{esc(image)}" alt="Algemeen sfeerbeeld bij de massagekeuze" loading="lazy"><figcaption>{esc(label)}</figcaption></figure><div class="choice-shell"><div class="choice-progress"><span id="choiceProgressText">Vraag 1 van 5</span><div class="choice-progress-track"><span id="choiceProgressBar"></span></div></div>'''+''.join(blocks)+'''<div class="choice-result" id="choiceResult" hidden><div class="eyebrow">Beste match</div><h3 id="choiceResultTitle"></h3><p id="choiceResultText"></p><div class="choice-result-actions"><a class="btn" id="choiceResultBook" href="#boeken">Afspraak maken</a><a class="btn btn-outline" id="choiceResultDetail" href="#massages">Bekijk behandeling</a></div><button type="button" class="text-button choice-restart" id="choiceRestart">Opnieuw kiezen</button></div></div></div></div></section>'''


def prices_section(treatments):
    rows=[]
    for t in active_treatments(treatments):
        prices=' · '.join(money(d['price']) for d in (t.get('durations') or []))
        rows.append(f'<div class="price-row"><strong>{esc(t.get("name"))}</strong><span>{prices}</span></div>')
    return '<section class="section" id="prijzen"><div class="container"><div class="section-head"><div><div class="eyebrow">Prijzen</div><h2>Duidelijk vooraf</h2></div><a class="btn btn-outline" href="#boeken">Boek afspraak</a></div><div class="price-list">'+''.join(rows)+'<p class="price-note">Kies de gewenste duur in het reserveringssysteem.</p></div></div></section>'

def about_section(site):
    a=site['about']; facts=''.join(f'<div class="about-fact"><strong>{esc(x)}</strong></div>' for x in a.get('facts',[]))
    return f'''<section class="section section-soft" id="over"><div class="container about-grid"><div class="about-photo"><img src="{esc(a.get('image'))}" alt="{esc(a.get('imageAlt'))}" loading="lazy"><span class="media-label">Baitan</span></div><div class="about-copy"><div class="eyebrow">{esc(a.get('kicker'))}</div><h2>{esc(a.get('title'))}</h2><p>{esc(a.get('text'))}</p><div class="about-facts">{facts}</div></div></div></section>'''

def gallery_section(site):
    items=[]
    for i,item in enumerate(site.get('gallery') or []):
        cls=' gallery-item-wide' if i==0 else ''
        label=f'<span class="media-label">{esc(item.get("label"))}</span>' if item.get('label') else ''
        items.append(f'''<figure class="gallery-item{cls}"><img src="{esc(item.get('image'))}" alt="{esc(item.get('alt'))}" loading="lazy" decoding="async">{label}</figure>''')
    if not items:
        return ''
    return '<section class="section gallery-section" id="sfeer"><div class="container"><div class="section-head"><div><div class="eyebrow">Sfeer</div><h2>Even uit de drukte.</h2></div><p>Echte Baitan-beelden worden als Baitan aangeduid. Aanvullende beelden zijn algemene sfeerbeelden.</p></div><div class="gallery-grid">'+''.join(items)+'</div></div></section>'

def gift_section(site):
    blocks=[]
    wa=str(site.get('whatsappUrl') or '').rstrip('/')
    gift_href=(wa+'?text=Hallo%20Baitan%2C%20ik%20wil%20graag%20informatie%20over%20een%20cadeaubon.') if wa else 'tel:'+str(site.get('phoneHref') or '')
    g=site.get('giftCard',{})
    if g.get('enabled'):
        blocks.append(f'''<div class="gift-block"><h3>{esc(g.get('title'))}</h3><p>{esc(g.get('text'))}</p><a class="btn btn-light" href="{esc(gift_href)}" target="_blank" rel="noopener">Vraag via WhatsApp</a></div>''')
    l=site.get('loyalty',{})
    if l.get('enabled'):
        blocks.append(f'''<div class="gift-block"><h3>{esc(l.get('title'))}</h3><p>{esc(l.get('text'))}</p><a class="btn btn-light" href="#contact">{esc(l.get('button'))}</a></div>''')
    if not blocks: return ''
    image=g.get('image') or site.get('hero',{}).get('image')
    image_alt=g.get('imageAlt') or 'Sfeerbeeld wellness'
    return f'''<section class="section section-dark" id="cadeaubon"><div class="container gift-shell"><figure class="gift-visual"><img src="{esc(image)}" alt="{esc(image_alt)}" loading="lazy"><figcaption>Sfeerbeeld</figcaption></figure><div><div class="eyebrow">Cadeau &amp; voordeel</div><div class="gift-grid">{''.join(blocks)}</div></div></div></section>'''


def reviews_section(site):
    r=site['reviews']
    write_btn=f'<a class="btn btn-outline" href="{esc(r.get("writeUrl"))}" target="_blank" rel="noopener">Schrijf een review</a>' if r.get('writeUrl') else ''
    return f'''<section class="section" id="reviews"><div class="container"><div class="review-band"><div><div class="eyebrow">Google Reviews</div><div class="rating-big">{esc(r.get('rating'))}</div><p class="rating-caption">{esc(r.get('count'))} Google-reviews</p></div><div class="review-actions"><a class="btn btn-outline" href="{esc(r.get('url'))}" target="_blank" rel="noopener">{esc(r.get('button'))}</a>{write_btn}</div></div></div></section>'''

def faq_section(site):
    items=[]
    for x in site.get('faq',[]):
        items.append(f'''<div class="faq-item"><button class="faq-question" aria-expanded="false">{esc(x.get('question'))}<span class="faq-icon" aria-hidden="true">+</span></button><div class="faq-answer"><div><p>{esc(x.get('answer'))}</p></div></div></div>''')
    return '<section class="section section-soft" id="faq"><div class="container"><div class="section-head"><div><div class="eyebrow">FAQ</div><h2>Goed om te weten</h2></div></div><div class="faq-list">'+''.join(items)+'</div></div></section>'

def contact_section(site):
    c=site['contact']; o=site['opening']
    return f'''<section class="section" id="contact"><div class="container contact-grid"><div class="contact-details"><div class="eyebrow">{esc(c.get('kicker'))}</div><h2>{esc(site.get('businessName'))}</h2><div class="detail-row"><span class="detail-label">Adres</span><div class="detail-value">{esc(site.get('addressLine1'))}<br>{esc(site.get('postalCity'))}</div></div><div class="detail-row"><span class="detail-label">Telefoon</span><div class="detail-value"><a href="tel:{esc(site.get('phoneHref'))}">{esc(site.get('phoneDisplay'))}</a></div></div><div class="detail-row"><span class="detail-label">E-mail</span><div class="detail-value"><a href="mailto:{esc(site.get('email'))}">{esc(site.get('email'))}</a></div></div><table class="hours" aria-label="Openingstijden"><tbody><tr><td>{esc(o.get('weekdayLabel'))}</td><td>{esc(o.get('weekdayOpen'))} — {esc(o.get('weekdayClose'))}</td></tr><tr><td>{esc(o.get('weekendLabel'))}</td><td>{esc(o.get('weekendOpen'))} — {esc(o.get('weekendClose'))}</td></tr></tbody></table><div class="contact-actions"><a class="btn" href="{esc(c.get('routeUrl'))}" target="_blank" rel="noopener">Route naar Baitan</a><a class="btn btn-outline" href="#boeken">Boek afspraak</a></div></div><div class="map-consent" data-map-url="{esc(c.get('mapEmbedUrl'))}"><div class="map-consent-inner"><div class="eyebrow">Google Maps</div><h3>Bekijk Baitan op de kaart</h3><p>De interactieve kaart wordt pas geladen nadat je hiervoor kiest.</p><button class="btn btn-outline load-map" type="button">Kaart laden</button></div></div></div></section>'''

def footer(site):
    return f'''<footer class="footer"><div class="container"><div class="footer-grid"><div><a class="brand" href="/"><span class="brand-mark"><span>B</span></span><span class="brand-name">BAITAN</span></a><p style="max-width:330px;margin-top:20px">{esc(site.get('tagline'))}</p></div><div><h4>Navigatie</h4><div class="footer-links"><a href="/massages">Massages</a><a href="/prijzen">Prijzen</a><a href="/#massagekeuze">Massagekeuze</a><a href="/#boeken">Boeken</a></div></div><div><h4>Contact</h4><div class="footer-links"><a href="tel:{esc(site.get('phoneHref'))}">{esc(site.get('phoneDisplay'))}</a><a href="mailto:{esc(site.get('email'))}">{esc(site.get('email'))}</a><span>{esc(site.get('addressLine1'))}</span><span>{esc(site.get('postalCity'))}</span></div></div><div><h4>Informatie</h4><div class="footer-links"><button class="footer-link-button" type="button" data-legal-modal="terms">Algemene voorwaarden</button><button class="footer-link-button" type="button" data-legal-modal="privacy">Privacy &amp; cookies</button><button class="footer-link-button" type="button" data-legal-modal="cancel">Annuleren &amp; afspraken</button><button class="footer-link-button" type="button" data-legal-modal="business">Bedrijfsgegevens</button></div></div></div><div class="footer-bottom"><span>© {esc(site.get('businessName'))}</span><span>KVK {esc(site.get('kvk'))} · BTW {esc(site.get('btw'))}</span></div></div></footer><dialog class="site-dialog legal-dialog" id="legalDialog" aria-labelledby="legalDialogTitle"><button class="dialog-close" type="button" data-dialog-close aria-label="Sluiten">×</button><div class="dialog-content"><div class="eyebrow">Baitan</div><h2 id="legalDialogTitle"></h2><div id="legalDialogBody"></div><a class="text-link" id="legalDialogLink" href="/voorwaarden">Lees volledige informatie <span>→</span></a></div></dialog>'''


def schema(site):
    o=site['opening']
    canonical=str(site.get('seo',{}).get('canonical') or '').rstrip('/')+'/'
    business={
        "@type":"HealthAndBeautyBusiness",
        "@id":canonical+"#business",
        "name":site.get('businessName'),
        "url":canonical,
        "telephone":site.get('phoneHref'),
        "email":site.get('email'),
        "image":site.get('seo',{}).get('ogImage') or site.get('hero',{}).get('image'),
        "address":{"@type":"PostalAddress","streetAddress":site.get('addressLine1'),"postalCode":"2904 EP","addressLocality":"Capelle aan den IJssel","addressCountry":"NL"},
        "openingHoursSpecification":[
            {"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],"opens":o.get('weekdayOpen'),"closes":o.get('weekdayClose')},
            {"@type":"OpeningHoursSpecification","dayOfWeek":["Saturday","Sunday"],"opens":o.get('weekendOpen'),"closes":o.get('weekendClose')}
        ]
    }
    website={"@type":"WebSite","@id":canonical+"#website","url":canonical,"name":site.get('businessName'),"inLanguage":"nl-NL"}
    payload={"@context":"https://schema.org","@graph":[business,website]}
    return '<script type="application/ld+json">'+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'</script>'

def subpage_head(site, title, description, canonical, breadcrumbs=None, noindex=False):
    image=esc(site.get('seo',{}).get('ogImage') or site.get('hero',{}).get('image'))
    robots='<meta name="robots" content="noindex,follow">' if noindex else ''
    breadcrumb_schema=''
    if breadcrumbs:
        items=[]
        for pos,(name,url) in enumerate(breadcrumbs,1):
            items.append({"@type":"ListItem","position":pos,"name":name,"item":url})
        breadcrumb_schema='<script type="application/ld+json">'+json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":items},ensure_ascii=False,separators=(',',':'))+'</script>'
    return f"""<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}">{robots}<link rel="canonical" href="{esc(canonical)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="website"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{image}"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/styles.css">{breadcrumb_schema}</head><body>"""

def subpage_header():
    return """<a class="skip-link" href="#main">Ga naar inhoud</a><header class="header"><div class="container nav"><a class="brand" href="/" aria-label="Baitan home"><span class="brand-mark"><span>B</span></span><span class="brand-name">BAITAN</span></a><nav class="nav-links" aria-label="Hoofdnavigatie"><a class="nav-link" href="/massages">Behandelingen</a><a class="nav-link" href="/#massagekeuze">Massagekeuze</a><a class="nav-link" href="/prijzen">Prijzen</a><a class="nav-link" href="/#reviews">Reviews</a><a class="nav-link" href="/contact">Contact</a></nav><div class="nav-actions"><a class="btn" href="/#boeken">Boek afspraak</a><button class="menu-toggle" aria-label="Open menu" aria-expanded="false"><span></span><span></span></button></div></div></header>"""

def treatment_page(site, treatment, treatments):
    base=str(site['seo']['canonical']).rstrip('/')
    slug=str(treatment.get('slug') or '').strip('/')
    canonical=base+'/'+slug
    rows=[]
    for d in treatment.get('durations',[]):
        rows.append(f'<div class="price-row"><strong>{int(d["minutes"])} minuten</strong><span>{money(d["price"])}</span></div>')
    feature_items=''.join(f'<li>{esc(x)}</li>' for x in treatment.get('features',[]))
    related=[]
    for other in active_treatments(treatments):
        if other.get('id') != treatment.get('id'):
            related.append(f'<a class="related-treatment" href="/{esc(other.get("slug"))}"><span>{esc(other.get("name"))}</span><span>→</span></a>')
    title=treatment.get('seoTitle') or (str(treatment.get('name'))+' | Baitan')
    description=treatment.get('seoDescription') or treatment.get('description') or ''
    breadcrumbs=[("Home",base+"/"),("Massages",base+"/massages"),(treatment.get('name'),canonical)]
    booking_url=str(site.get('booking',{}).get('treatwellBookingUrl') or '/#boeken')
    external=' target="_blank" rel="noopener"' if booking_url.startswith('http') else ''
    image=treatment.get('image') or site.get('hero',{}).get('image')
    label=treatment.get('imageLabel') or ''
    label_html=f'<span class="media-label">{esc(label)}</span>' if label else ''
    body=f"""<main id="main"><section class="detail-hero"><div class="container detail-hero-grid"><div><div class="eyebrow">Baitan · Capelle aan den IJssel</div><h1>{esc(treatment.get('name'))} in Capelle aan den IJssel</h1><p>{esc(treatment.get('description'))}</p><div class="hero-actions"><a class="btn" href="{esc(booking_url)}"{external}>Afspraak maken</a><a class="btn btn-outline" href="/massages">Alle massages</a></div></div><figure class="detail-hero-photo"><img src="{esc(image)}" alt="{esc(treatment.get('imageAlt') or treatment.get('name'))}">{label_html}</figure></div></section><section class="section"><div class="container detail-layout"><article class="detail-copy"><div class="eyebrow">Over de behandeling</div><h2>{esc(treatment.get('name'))}</h2><p>{esc(treatment.get('detailText') or treatment.get('description'))}</p><ul class="feature-list">{feature_items}</ul></article><aside class="detail-price"><div class="eyebrow">Duur &amp; prijs</div><div class="price-list">{''.join(rows)}</div><a class="btn booking-submit" href="{esc(booking_url)}"{external}>Afspraak maken</a></aside></div></section><section class="section section-soft"><div class="container"><div class="section-head"><div><div class="eyebrow">Andere behandelingen</div><h2>Bekijk ook</h2></div></div><div class="related-grid">{''.join(related)}</div></div></section></main>"""
    return subpage_head(site,title,description,canonical,breadcrumbs)+subpage_header()+body+footer(site)+'<script>window.BAITAN_SITE='+json.dumps(site,ensure_ascii=False).replace('</','<\\/')+';window.BAITAN_TREATMENTS='+json.dumps(active_treatments(treatments),ensure_ascii=False).replace('</','<\\/')+';</script><script src="/app.js"></script></body></html>'

def massages_page(site, treatments):
    base=str(site['seo']['canonical']).rstrip('/')
    canonical=base+'/massages'
    cards=[]
    for t in active_treatments(treatments):
        prices=t.get('durations',[])
        start=min((float(d['price']) for d in prices), default=0)
        image=t.get('image') or site.get('hero',{}).get('image')
        label=t.get('imageLabel') or ''
        label_html=f'<span class="media-label">{esc(label)}</span>' if label else ''
        cards.append(f'<a class="seo-card seo-card-visual" href="/{esc(t.get("slug"))}"><div class="seo-card-media"><img src="{esc(image)}" alt="{esc(t.get("imageAlt") or t.get("name"))}" loading="lazy">{label_html}</div><div class="seo-card-copy"><div class="eyebrow">Vanaf {money(start)}</div><h2>{esc(t.get("name"))}</h2><p>{esc(t.get("description"))}</p><span>Bekijk behandeling →</span></div></a>')
    body='<main id="main"><section class="detail-hero"><div class="container"><div class="eyebrow">Baitan Thai Massage</div><h1>Massages in Capelle aan den IJssel</h1><p>Bekijk het actuele massageaanbod van Baitan met duur en prijzen.</p></div></section><section class="section"><div class="container seo-card-grid">'+''.join(cards)+'</div></section></main>'
    return subpage_head(site,'Massages in Capelle aan den IJssel | Baitan','Bekijk Thaise massage, aromatherapie, sportmassage, hot stone en duo-massage bij Baitan in Capelle aan den IJssel.',canonical,[("Home",base+"/"),("Massages",canonical)])+subpage_header()+body+footer(site)+'<script>window.BAITAN_SITE='+json.dumps(site,ensure_ascii=False).replace('</','<\\/')+';window.BAITAN_TREATMENTS='+json.dumps(active_treatments(treatments),ensure_ascii=False).replace('</','<\\/')+';</script><script src="/app.js"></script></body></html>'

def prices_page(site, treatments):
    base=str(site['seo']['canonical']).rstrip('/')
    canonical=base+'/prijzen'
    rows=[]
    for t in active_treatments(treatments):
        prices=' · '.join(f'{int(d["minutes"])} min {money(d["price"])}' for d in t.get('durations',[]))
        rows.append(f'<div class="price-row"><strong><a href="/{esc(t.get("slug"))}">{esc(t.get("name"))}</a></strong><span>{prices}</span></div>')
    body='<main id="main"><section class="detail-hero"><div class="container"><div class="eyebrow">Baitan Thai Massage</div><h1>Massageprijzen in Capelle aan den IJssel</h1><p>Actuele duur en prijzen van de behandelingen van Baitan.</p></div></section><section class="section"><div class="container"><div class="price-list wide-price-list">'+''.join(rows)+'</div><div class="hero-actions"><a class="btn" href="/#boeken">Boek afspraak</a><a class="btn btn-outline" href="/massages">Bekijk behandelingen</a></div></div></section></main>'
    return subpage_head(site,'Massage Prijzen Capelle aan den IJssel | Baitan','Bekijk de actuele prijzen van Baitan Thai Massage in Capelle aan den IJssel voor 60, 90 en 120 minuten.',canonical,[("Home",base+"/"),("Prijzen",canonical)])+subpage_header()+body+footer(site)+'<script src="/app.js"></script></body></html>'

def contact_page(site):
    base=str(site['seo']['canonical']).rstrip('/')
    canonical=base+'/contact'
    body='<main id="main"><section class="detail-hero"><div class="container"><div class="eyebrow">Contact & route</div><h1>Baitan Thai Massage in Capelle aan den IJssel</h1><p>Hollandsch Diep 71–73, 2904 EP Capelle aan den IJssel.</p></div></section>'+contact_section(site)+'</main>'
    return subpage_head(site,'Contact Baitan Thai Massage | Capelle aan den IJssel','Contact, openingstijden, route en adres van Baitan Thai Massage aan het Hollandsch Diep in Capelle aan den IJssel.',canonical,[("Home",base+"/"),("Contact",canonical)])+subpage_header()+body+footer(site)+'<script src="/app.js"></script></body></html>'

def not_found_page(site):
    base=str(site['seo']['canonical']).rstrip('/')
    body='''<main id="main"><section class="detail-hero"><div class="container"><div class="eyebrow">404</div><h1>Pagina niet gevonden</h1><p>Ga terug naar Baitan of bekijk de massages en prijzen.</p><div class="hero-actions"><a class="btn" href="/">Home</a><a class="btn btn-outline" href="/massages">Massages</a></div></div></section></main>'''
    return subpage_head(site,'Pagina niet gevonden | Baitan','Deze pagina bestaat niet of is verplaatst.',base+'/404',noindex=True)+subpage_header()+body+footer(site)+'</body></html>'

def build():
    site=load_json('data/site.json')
    treatments=load_json('data/treatments.json')
    tpl=(ROOT/'index.template.html').read_text(encoding='utf-8')
    replacements={
      'SEO_TITLE':esc(site['seo']['title']),
      'SEO_DESCRIPTION':esc(site['seo']['description']),
      'OG_TITLE':esc(site['seo']['ogTitle']),
      'OG_DESCRIPTION':esc(site['seo']['ogDescription']),
      'OG_IMAGE':esc(site['seo'].get('ogImage') or site.get('hero',{}).get('image')),
      'CANONICAL':esc(site['seo']['canonical']),
      'SCHEMA_JSON':schema(site),
      'HERO':hero(site),
      'TRUSTBAR':trustbar(site),
      'BOOKING':booking(site,treatments),
      'TREATMENTS':treatments_section(site,treatments),
      'MASSAGE_CHOICE':massage_choice_section(site),
      'PRICES':prices_section(treatments),
      'ABOUT':about_section(site),
      'GALLERY':gallery_section(site),
      'GIFT':gift_section(site),
      'REVIEWS':reviews_section(site),
      'FAQ':faq_section(site),
      'CONTACT':contact_section(site),
      'FOOTER':footer(site),
      'DATA_SCRIPT':'<script>window.BAITAN_SITE='+json.dumps(site,ensure_ascii=False).replace('</','<\\/')+';window.BAITAN_TREATMENTS='+json.dumps(active_treatments(treatments),ensure_ascii=False).replace('</','<\\/')+';</script>'
    }
    for key,value in replacements.items():
        tpl=tpl.replace('{{'+key+'}}',value)
    if '{{' in tpl:
        raise RuntimeError('Onvervangen template-token gevonden')

    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST/'index.html').write_text(tpl,encoding='utf-8')
    base=str(site['seo']['canonical']).rstrip('/')
    (DIST/'massages.html').write_text(massages_page(site,treatments),encoding='utf-8')
    (DIST/'prijzen.html').write_text(prices_page(site,treatments),encoding='utf-8')
    (DIST/'contact.html').write_text(contact_page(site),encoding='utf-8')
    for treatment in active_treatments(treatments):
        slug=str(treatment.get('slug') or '').strip('/')
        if slug:
            (DIST/(slug+'.html')).write_text(treatment_page(site,treatment,treatments),encoding='utf-8')
    (DIST/'404.html').write_text(not_found_page(site),encoding='utf-8')

    urls=[base+'/',base+'/massages',base+'/prijzen',base+'/contact',base+'/voorwaarden',base+'/privacy']
    urls.extend(base+'/'+str(t.get('slug')).strip('/') for t in active_treatments(treatments) if t.get('slug'))
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap+=''.join('  <url><loc>'+html.escape(url)+'</loc></url>\n' for url in urls)
    sitemap+='</urlset>\n'
    (DIST/'sitemap.xml').write_text(sitemap,encoding='utf-8')
    (DIST/'robots.txt').write_text('User-agent: *\nAllow: /\nDisallow: /admin\nSitemap: '+base+'/sitemap.xml\n',encoding='utf-8')
    for name in ['styles.css','app.js','privacy.html','voorwaarden.html','favicon.svg']:
        if (ROOT/name).exists():
            shutil.copy2(ROOT/name,DIST/name)
    if (ROOT/'admin').exists(): shutil.copytree(ROOT/'admin',DIST/'admin')
    if (ROOT/'assets').exists(): shutil.copytree(ROOT/'assets',DIST/'assets')
    shutil.copytree(ROOT/'data',DIST/'data')
    print('Baitan website gebouwd in dist/')

if __name__=='__main__':
    build()
