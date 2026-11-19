#!/usr/bin/env python3
"""Build the original, static Laurel Run discovery-test website."""
from html import escape
from pathlib import Path
import json

from pages import PAGES

ROOT = Path(__file__).parent
SITE = ROOT / 'site'
HERO = '/assets/image-1.webp'
UTILITY = '/assets/image-2.webp'
CARGO = '/assets/image-3.webp'
EQUIPMENT = '/assets/image-4.webp'
FACTORY = '/assets/image-5.webp'

HOME = f'''
<section class="hero-intro">
  <div class="container">
    <p class="hero-kicker">Family-owned. Pennsylvania built. Since 1988.</p>
    <h1 class="hero-title">Trailers built for<br><span class="hero-accent">the work ahead</span></h1>
  </div>
</section>
<div class="hero-image"><img src="{HERO}" alt="A lineup of enclosed, utility, and equipment trailers at a workshop"></div>
<section class="section welcome-section">
  <div class="container split">
    <div class="split-media"><img src="{FACTORY}" alt="Fabrication inside a small trailer manufacturing workshop" loading="lazy"></div>
    <div class="split-copy">
      <p class="eyebrow">Pennsylvania trailer manufacturing</p>
      <h2>Welcome to<br>Laurel Run Trailer Works</h2>
      <div class="red-rule"></div>
      <p>From our shop in Hollow Glen, Pennsylvania, we build utility, enclosed cargo, and equipment trailers for work on the road and at the job site. Our family started Laurel Run in 1988 with a simple idea: make useful equipment and stand behind the people who use it.</p>
      <p>Today our team cuts, welds, paints, assembles, and checks trailers for a network of independent dealers. Each dealer can help you choose a model, discuss options, and arrange a purchase.</p>
      <a class="button" href="/about/index.html">Our story <span aria-hidden="true">→</span></a>
    </div>
  </div>
</section>
<section class="quote-band">
  <div class="container quote-band-inner"><div><p class="eyebrow">Ready for the next job?</p><h2>Have a trailer in mind?</h2><p>Explore the lineup, then connect with an independent dealer.</p></div><a class="button button-light" href="/trailers/index.html">Explore our trailers <span aria-hidden="true">→</span></a></div>
</section>
<section class="section section-alt">
  <div class="container">
    <div class="section-heading"><p class="eyebrow">Made for the way you work</p><h2>Find your trailer</h2><div class="red-rule"></div><p>From open utility trailers to enclosed cargo and equipment haulers, start with the style that fits your work.</p></div>
    <div class="cards-three">
      <article class="product-card"><a class="product-image" href="/trailers/trailfield.html"><img src="{UTILITY}" alt="Open utility trailer" loading="lazy"></a><div class="product-body"><p class="eyebrow">Open utility</p><h3>Trailfield</h3><p>A versatile open deck and rear loading gate for everyday hauling.</p><a class="text-link" href="/trailers/trailfield.html">View trailer <span aria-hidden="true">→</span></a></div></article>
      <article class="product-card"><a class="product-image" href="/trailers/enclosure.html"><img src="{CARGO}" alt="Enclosed cargo trailer" loading="lazy"></a><div class="product-body"><p class="eyebrow">Enclosed cargo</p><h3>Enclosure</h3><p>Covered room for tools and materials, built around a steel frame.</p><a class="text-link" href="/trailers/enclosure.html">View trailer <span aria-hidden="true">→</span></a></div></article>
      <article class="product-card"><a class="product-image" href="/trailers/workspan.html"><img src="{EQUIPMENT}" alt="Open equipment trailer with ramps" loading="lazy"></a><div class="product-body"><p class="eyebrow">Equipment</p><h3>Workspan</h3><p>A wider open deck with loading ramps for equipment and materials.</p><a class="text-link" href="/trailers/workspan.html">View trailer <span aria-hidden="true">→</span></a></div></article>
    </div>
  </div>
</section>
<section class="section dealer-block">
  <div class="container split">
    <div class="split-copy"><p class="eyebrow">People you can talk to</p><h2>Find an independent dealer</h2><div class="red-rule"></div><p>Laurel Run works with approximately 80 independent dealers. Dealers provide local product information, discuss available configurations, set retail prices, and handle purchases.</p><p>We do not sell trailers directly from the factory to retail customers.</p><a class="button" href="/dealers/index.html">Find a dealer <span aria-hidden="true">→</span></a></div>
    <div class="dealer-box"><span class="dealer-box-number">80<span>+</span></span><strong>Independent dealer network</strong><p>Browse our fictional network by state.</p><a class="text-link" href="/dealers/index.html">Browse dealer locations →</a></div>
  </div>
</section>
<section class="section section-alt"><div class="container split split-reverse"><div class="split-media"><img src="{CARGO}" alt="White enclosed cargo trailer" loading="lazy"></div><div class="split-copy"><p class="eyebrow">Made with care</p><h2>Built from the frame up</h2><div class="red-rule"></div><p>Our shop brings together steel frames, exterior panels, wiring, running gear, and finishing work. We check each trailer before it leaves the facility, with attention to the model and options ordered by the dealer.</p><p>Ask your dealer for the specifications, load label, and available options for the finished unit.</p><a class="button button-secondary" href="/resources/index.html">Owner resources <span aria-hidden="true">→</span></a></div></div></section>
'''

STATES = ['Delaware','Indiana','Kentucky','Maryland','New Jersey','New York','North Carolina','Ohio','Pennsylvania','Vermont','Virginia','West Virginia']
OPTIONS = ''.join(f'<option value="{escape(s)}">{escape(s)}</option>' for s in STATES)
DEALERS = f'''
<section class="page-hero"><div class="container"><p class="eyebrow">Local knowledge, independent dealers</p><h1 class="page-title">Find a Laurel Run dealer</h1><p>Find a fictional dealer in the network by state.</p></div></section>
<section class="section"><div class="container">
  <div class="content-grid"><div class="article-body"><p class="eyebrow">Our dealer network</p><h2>A dealer near your work</h2><div class="red-rule"></div><p>Laurel Run builds trailers for approximately 80 independent dealers. Each dealer sets its own retail prices and can discuss options, availability, purchases, and parts. There are no factory-direct retail sales.</p><p>This is a fictional dealer network for an academic test; there are no real business addresses, phone numbers, or directions.</p></div>
  <aside class="notice"><strong>How to use the directory</strong><p>Choose a state to view the fictional dealer names in our test records. Search is by state only; it does not calculate proximity.</p></aside></div>
  <form id="dealer-search-form" class="dealer-search"><label for="dealer-state">Choose a state</label><div><select id="dealer-state" name="state"><option value="">Choose a state</option>{OPTIONS}</select><button class="button" type="submit">Show dealers</button></div></form>
  <p class="dealer-summary" id="dealer-count">Showing four example dealers. Use the state search to explore the fictional directory.</p>
  <div class="dealer-results" id="dealer-results" aria-live="polite">
    <article class="dealer-card"><h3>Cedar Bend Trailer Sales</h3><p>Pennsylvania</p><small>DLR-0001 · Independent dealer</small></article>
    <article class="dealer-card"><h3>Maple Span Equipment</h3><p>New York</p><small>DLR-0002 · Independent dealer</small></article>
    <article class="dealer-card"><h3>Arrow Hollow Trailer Center</h3><p>Ohio</p><small>DLR-0003 · Independent dealer</small></article>
    <article class="dealer-card"><h3>Stonegate Trailer Outlet</h3><p>West Virginia</p><small>DLR-0004 · Independent dealer</small></article>
  </div>
  <p><a class="button button-secondary" href="/contact/dealer.html">Prepare a simulated dealer inquiry</a></p>
  <noscript><p>JavaScript is needed to filter the complete fictional directory; the four sample records above are available without it.</p></noscript>
</div></section>
'''

HEADER = '''
<div class="test-banner">Fictional company website · Created for discovery testing</div>
<header class="site-header">
  <div class="masthead container"><a class="brand" href="/" aria-label="Laurel Run Trailer Works home"><span class="brand-emblem" aria-hidden="true">LR</span><span class="brand-wordmark"><span>LAUREL RUN</span><small class="brand-sub">TRAILER WORKS &nbsp; • &nbsp; PENNSYLVANIA</small></span></a><p class="tagline">Family-owned since 1988</p></div>
  <div class="nav-shell"><div class="nav-inner container"><button class="nav-toggle" type="button" data-nav-toggle aria-expanded="false" aria-controls="main-menu">Menu <span aria-hidden="true">☰</span></button><nav id="main-menu" class="main-menu" data-main-menu aria-label="Main navigation"><a href="/">Home</a><a href="/trailers/index.html">Trailers</a><a href="/resources/index.html">Owners</a><a href="/about/index.html">Information</a><a href="/dealers/index.html">Find a dealer</a></nav><a class="nav-cta" href="/contact/index.html">Contact us <span aria-hidden="true">→</span></a></div></div>
</header>
'''

FOOTER = '''
<footer class="site-footer"><div class="container footer-grid">
  <div class="footer-brand"><a class="brand brand-footer" href="/"><span class="brand-emblem" aria-hidden="true">LR</span><span class="brand-wordmark"><span>LAUREL RUN</span><small class="brand-sub">TRAILER WORKS</small></span></a><p>Fictional trailer manufacturing<br>Hollow Glen, Pennsylvania</p><p class="footer-small">Family-owned since 1988.</p></div>
  <div><h3>Explore</h3><ul><li><a href="/trailers/index.html">Our trailers</a></li><li><a href="/about/index.html">Our story</a></li><li><a href="/dealers/index.html">Find a dealer</a></li><li><a href="/contact/index.html">Contact &amp; confirmation</a></li></ul></div>
  <div><h3>For owners</h3><ul><li><a href="/resources/index.html">Owner resources</a></li><li><a href="/resources/warranty.html">Warranty information</a></li><li><a href="/resources/trailer-care.html">Trailer care</a></li><li><a href="/resources/dealer-support.html">Dealer support</a></li></ul></div>
  <div><h3>Our trailers</h3><ul><li><a href="/trailers/trailfield.html">Trailfield Utility</a></li><li><a href="/trailers/enclosure.html">Enclosure Cargo</a></li><li><a href="/trailers/workspan.html">Workspan Equipment</a></li></ul></div>
</div><div class="container footer-bottom"><p>© 2026 Laurel Run Trailer Works, Inc. &nbsp;·&nbsp; Fictional academic simulation; no real sales or inquiries.</p><p><a href="/privacy/index.html">Privacy</a> &nbsp; | &nbsp; <a href="/terms/index.html">Terms</a></p></div></footer>
'''

PAGES['index.html'] = {'title':'Laurel Run Trailer Works | Pennsylvania Trailer Manufacturer','description':'Laurel Run is a family-owned Pennsylvania manufacturer of utility, enclosed cargo, and equipment trailers, sold through independent dealers.','body':HOME}
PAGES['dealers/index.html'] = {'title':'Find an Independent Dealer | Laurel Run Trailer Works','description':'Explore the fictional Laurel Run independent trailer dealer network by state. Dealers handle retail sales and product support.','body':DEALERS}

organization = {
    '@context': 'https://schema.org', '@type': 'Organization',
    'name': 'Laurel Run Trailer Works, Inc.',
    'description': 'Fictional family-owned Pennsylvania manufacturer of utility, enclosed cargo, and equipment trailers.',
    'foundingDate': '1988', 'numberOfEmployees': {'@type': 'QuantitativeValue', 'value': 50},
    'address': {'@type': 'PostalAddress', 'addressLocality': 'Hollow Glen', 'addressRegion': 'PA', 'addressCountry': 'US'},
    'industry': 'Trailer manufacturing',
}

for path, page in PAGES.items():
    target = SITE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    title, description, body = page['title'], page['description'], page['body']
    structured = '<script type="application/ld+json">' + json.dumps(organization).replace('</', '<\\/') + '</script>'
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)}</title><meta name="description" content="{escape(description, quote=True)}">
<meta property="og:type" content="website"><meta property="og:title" content="{escape(title, quote=True)}"><meta property="og:description" content="{escape(description, quote=True)}"><meta property="og:site_name" content="Laurel Run Trailer Works"><meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="/assets/styles.css"><script defer src="/assets/site.js"></script>{structured}</head><body>
<a class="skip-link" href="#main-content">Skip to content</a>{HEADER}<main id="main-content">{body}</main>{FOOTER}</body></html>'''
    target.write_text(document, encoding='utf-8')

routes = []
for path, page in sorted(PAGES.items()):
    routes.append({'path': '/' if path == 'index.html' else '/' + path, 'title': page['title']})
(SITE / 'manus-routes.json').write_text(json.dumps({'routes':routes}, indent=2) + '\n', encoding='utf-8')
print(f'Built {len(PAGES)} complete static pages in {SITE}')
