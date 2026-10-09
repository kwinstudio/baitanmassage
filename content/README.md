# Inhoud in Markdown

- `kennisbank/*.md` → artikelen op /massagegids/<slug>
- `paginas/*.md` → losse landingspagina's op /<slug>

Bovenaan elk bestand staat een blok tussen `---` met instellingen:

| Veld | Betekenis |
|---|---|
| slug | URL-deel, bijv. `wat-is-een-thaise-massage` |
| title | SEO-titel (max ± 60 tekens) |
| description | Meta description (max ± 155 tekens) |
| h1 | Hoofdtitel op de pagina |
| lead | Introductiezin onder de titel |
| image / imageAlt | Foto (naam uit assets/images, zonder extensie) en beschrijving |
| date / updated | Publicatie- en wijzigingsdatum (JJJJ-MM-DD) |
| related | Behandelingen om naar te linken (thai, aroma, sport, hotstone, duo, scrub) |
| faq | Herhaalbaar: `Vraag | Antwoord` → komt als FAQ op de pagina en in het schema |
| order | Volgorde in overzichten |

Opmaak in de tekst: `## Kop`, `### Subkop`, alinea's, lijsten met `- `, genummerd met `1. `, **vet** en [links](/prijzen).
