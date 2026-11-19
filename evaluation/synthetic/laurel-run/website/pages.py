"""Crawler-readable page content for the fictional Laurel Run website.

A separate site generator supplies the shared document shell, header, footer,
styles, and local owner-confirmation interaction. This module performs no I/O.
"""

from html import escape


UTILITY_IMAGE = "/assets/image-2.webp"
CARGO_IMAGE = "/assets/image-3.webp"
EQUIPMENT_IMAGE = "/assets/image-4.webp"
FACTORY_IMAGE = "/assets/image-5.webp"


def _hero(eyebrow, title, ancestors=()):
    """Return a consistent page heading, breadcrumb, and visible demo notice."""
    links = ['<a href="/">Home</a>']
    links.extend(
        f'<a href="{escape(path, quote=True)}">{escape(label)}</a>'
        for label, path in ancestors
    )
    links.append(f'<span aria-current="page">{escape(title)}</span>')
    trail = ' <span aria-hidden="true">/</span> '.join(links)
    return f'''<section class="page-hero">
  <div class="container">
    <nav class="breadcrumb" aria-label="Breadcrumb">{trail}</nav>
    <p class="eyebrow">{escape(eyebrow)}</p>
    <h1 class="page-title">{escape(title)}</h1>
    <p class="notice" role="note">Fictional demonstration: Laurel Run Trailer Works, its people, dealers, and products are invented. No purchases or messages are processed.</p>
  </div>
</section>
'''


PAGES = {
    "trailers/index.html": {
        "title": "Trailers | Laurel Run Trailer Works",
        "description": "Explore three fictional Laurel Run trailer models: the Trailfield utility, Enclosure cargo, and Workspan equipment trailers.",
        "body": _hero("Find the right kind of trailer", "Our Trailers") + f'''<section class="section">
  <div class="container">
    <div class="article-body">
      <h2>Built for different kinds of work</h2>
      <p>From an open utility deck to enclosed storage and equipment hauling, the Laurel Run lineup starts with the job you need to do. Browse the three models below, then consider the load, the tow vehicle, and the finished trailer's labels together.</p>
      <p>Laurel Run works through approximately 80 independent dealers and does not sell directly to retail customers. Dealers set their own retail prices and can discuss a specific configuration.</p>
    </div>
    <div class="content-grid">
      <article class="info-card">
        <a href="/trailers/trailfield.html"><img class="model-image" src="{UTILITY_IMAGE}" alt="Fictional Trailfield open utility trailer" loading="lazy"></a>
        <p class="eyebrow">Open utility</p>
        <h3><a class="text-link" href="/trailers/trailfield.html">Trailfield 6 × 12</a></h3>
        <p>An open steel trailer with one electric-braked axle and a rear loading gate for general-purpose hauling.</p>
        <a class="text-link" href="/trailers/trailfield.html">Explore Trailfield</a>
      </article>
      <article class="info-card">
        <a href="/trailers/enclosure.html"><img class="model-image" src="{CARGO_IMAGE}" alt="Fictional Enclosure enclosed cargo trailer" loading="lazy"></a>
        <p class="eyebrow">Enclosed cargo</p>
        <h3><a class="text-link" href="/trailers/enclosure.html">Enclosure 7 × 14</a></h3>
        <p>A tandem-axle enclosed cargo trailer with a steel frame, aluminum exterior, and plywood lining.</p>
        <a class="text-link" href="/trailers/enclosure.html">Explore Enclosure</a>
      </article>
      <article class="info-card">
        <a href="/trailers/workspan.html"><img class="model-image" src="{EQUIPMENT_IMAGE}" alt="Fictional Workspan open equipment trailer" loading="lazy"></a>
        <p class="eyebrow">Equipment</p>
        <h3><a class="text-link" href="/trailers/workspan.html">Workspan 82 in × 18 ft</a></h3>
        <p>A wide open steel deck with loading ramps and tandem electric-braked axles for equipment hauling.</p>
        <a class="text-link" href="/trailers/workspan.html">Explore Workspan</a>
      </article>
    </div>
    <p><a class="button" href="/dealers/index.html">Explore the dealer network</a> <a class="button button-secondary" href="/resources/index.html">Browse owner resources</a></p>
  </div>
</section>''',
    },
    "trailers/trailfield.html": {
        "title": "Trailfield 6 × 12 Utility Trailer | Laurel Run",
        "description": "Get to know the fictional Trailfield 6 × 12 open steel utility trailer, with a rear gate and a single electric-braked axle.",
        "body": _hero("Open utility trailer", "Trailfield 6 × 12", (("Trailers", "/trailers/index.html"),)) + f'''<section class="section">
  <div class="container model-layout">
    <div>
      <img class="model-image" src="{UTILITY_IMAGE}" alt="Fictional Trailfield open utility trailer with rear loading gate">
      <p class="notice">Illustration of a fictional model. The pictured configuration is not a specification or availability guarantee.</p>
    </div>
    <div class="article-body">
      <h2>A practical open deck</h2>
      <p>The Trailfield is a straightforward utility trailer for everyday hauling. Its 6-foot by 12-foot open steel platform and rear loading gate give equipment and materials a place to ride without an enclosed body. The single axle has electric brakes. Think of it as a starting point for general-purpose jobs, with the trailer, load, and tow vehicle selected as a complete combination.</p>
      <h2>At a glance</h2>
      <dl class="spec-list">
        <div><dt>Nominal size</dt><dd>6 feet × 12 feet</dd></div>
        <div><dt>Construction</dt><dd>Open steel utility trailer</dd></div>
        <div><dt>Axle</dt><dd>One 3,500-lb-rated axle with electric brakes</dd></div>
        <div><dt>Loading</dt><dd>Rear loading gate</dd></div>
      </dl>
      <p>The axle rating is a component rating, not the trailer's gross vehicle weight rating (GVWR) or its available payload. The completed unit's certification and load labels determine the applicable ratings; the trailer's own weight, installed equipment, and other factors affect what it can carry. Never infer payload from dimensions or an axle rating.</p>
      <h2>Plan for the load</h2>
      <p>Consider the shape and weight of what you intend to move, how it will be secured, the gate opening, and the tow vehicle and hitch ratings. A dealer can explain the available configuration and whether options such as a spare-tire mount or upgraded jack are offered for a particular unit. Confirm all details on the specific trailer before making a decision.</p>
      <p><a class="button" href="/dealers/index.html">Explore the dealer network</a> <a class="button button-secondary" href="/resources/trailer-care.html">Trailer care guide</a></p>
      <p><a class="text-link" href="/trailers/index.html">Back to all trailers</a></p>
    </div>
  </div>
</section>''',
    },
    "trailers/enclosure.html": {
        "title": "Enclosure 7 × 14 Cargo Trailer | Laurel Run",
        "description": "Explore the fictional Enclosure 7 × 14 tandem-axle cargo trailer, with a steel frame, aluminum exterior, and plywood lining.",
        "body": _hero("Enclosed cargo trailer", "Enclosure 7 × 14", (("Trailers", "/trailers/index.html"),)) + f'''<section class="section">
  <div class="container model-layout">
    <div>
      <img class="model-image" src="{CARGO_IMAGE}" alt="Fictional Enclosure tandem-axle enclosed cargo trailer">
      <p class="notice">Illustration of a fictional model. The pictured configuration is not a specification or availability guarantee.</p>
    </div>
    <div class="article-body">
      <h2>Room for the things you bring along</h2>
      <p>The Enclosure is a 7-foot by 14-foot enclosed cargo trailer for tools, supplies, and other materials. A steel frame supports an aluminum exterior and a plywood-lined interior. Its tandem-axle layout, rear door, and electric-braked axles make it a useful starting point when an enclosed space is important to the job.</p>
      <h2>At a glance</h2>
      <dl class="spec-list">
        <div><dt>Nominal size</dt><dd>7 feet × 14 feet</dd></div>
        <div><dt>Frame</dt><dd>Steel</dd></div>
        <div><dt>Exterior and lining</dt><dd>Aluminum exterior; plywood interior lining</dd></div>
        <div><dt>Running gear</dt><dd>Tandem axles with electric brakes</dd></div>
        <div><dt>Access</dt><dd>Rear door</dd></div>
      </dl>
      <p>Nominal exterior dimensions do not establish the clear interior dimensions, door opening, or usable load. These can vary with the finished configuration. Check the certification and load labels on the completed unit, and confirm that the tow vehicle, hitch, and brake system are suited to the combination.</p>
      <h2>Make the space work for you</h2>
      <p>Before choosing a configuration, consider the size and weight of your cargo, the clearances needed to load it, and how items will be restrained. A dealer can discuss current colors and available options, along with the dimensions and specifications of a particular trailer. Keep doors secured for travel and follow the instructions supplied with the finished unit.</p>
      <p><a class="button" href="/dealers/index.html">Explore the dealer network</a> <a class="button button-secondary" href="/resources/trailer-care.html">Trailer care guide</a></p>
      <p><a class="text-link" href="/trailers/index.html">Back to all trailers</a></p>
    </div>
  </div>
</section>''',
    },
    "trailers/workspan.html": {
        "title": "Workspan Equipment Trailer | Laurel Run",
        "description": "See the fictional Workspan 82-inch by 18-foot open equipment trailer, with a steel deck, ramps, and tandem electric-braked axles.",
        "body": _hero("Open equipment trailer", "Workspan 82 in × 18 ft", (("Trailers", "/trailers/index.html"),)) + f'''<section class="section">
  <div class="container model-layout">
    <div>
      <img class="model-image" src="{EQUIPMENT_IMAGE}" alt="Fictional Workspan open steel-deck equipment trailer with ramps">
      <p class="notice">Illustration of a fictional model. The pictured configuration is not a specification or availability guarantee.</p>
    </div>
    <div class="article-body">
      <h2>A wider deck for equipment</h2>
      <p>The Workspan brings an 82-inch-wide by 18-foot open steel deck together with loading ramps and a tandem-axle arrangement. The two axles are each rated at 5,200 pounds and have electric brakes. It is designed as a starting point for equipment-hauling conversations, where the complete load, its dimensions, and the towing combination all matter.</p>
      <h2>At a glance</h2>
      <dl class="spec-list">
        <div><dt>Nominal deck</dt><dd>82 inches wide × 18 feet long</dd></div>
        <div><dt>Deck and frame</dt><dd>Open steel construction</dd></div>
        <div><dt>Axles</dt><dd>Two 5,200-lb-rated axles with electric brakes</dd></div>
        <div><dt>Loading</dt><dd>Ramps</dd></div>
      </dl>
      <p>Each axle's rating describes that component; adding axle ratings does not establish this trailer's GVWR or payload. Check the completed trailer's certification and load labels and the limits of the tow vehicle, hitch, and other components. The weight of the trailer and its installed equipment affects available payload.</p>
      <h2>Think through loading and securement</h2>
      <p>Discuss the equipment's weight, dimensions, ground clearance, and loading requirements with a dealer. Ask about ramp, tie-down, and coupler choices for the particular configuration, and verify that all equipment and attachment points are appropriate for the intended load. Follow the finished trailer's instructions and applicable securement rules before travel.</p>
      <p><a class="button" href="/dealers/index.html">Explore the dealer network</a> <a class="button button-secondary" href="/resources/trailer-care.html">Trailer care guide</a></p>
      <p><a class="text-link" href="/trailers/index.html">Back to all trailers</a></p>
    </div>
  </div>
</section>''',
    },
    "about/index.html": {
        "title": "About Us | Laurel Run Trailer Works",
        "description": "Read the fictional story of family-owned Laurel Run Trailer Works, founded in 1988 in the invented community of Hollow Glen, Pennsylvania.",
        "body": _hero("Our story", "About Laurel Run") + f'''<section class="section">
  <div class="container model-layout">
    <div class="article-body">
      <h2>A family story, built around useful work</h2>
      <p>Elwood Bellamy founded Laurel Run Trailer Works in 1988. He built the business around practical trailers and a relationship with independent dealers. He retired in 2018, and the Bellamy family continues to own the company.</p>
      <p>Today, Mara Bellamy is president and CEO, Owen Bellamy is plant manager, and Tessa Bellamy manages dealer sales. The fictional business has 50 employees and works with approximately 80 independent dealers. Dealers set their own retail prices; Laurel Run does not sell factory-direct to retail customers.</p>
      <h2>One Pennsylvania facility</h2>
      <p>Laurel Run operates its facility in Hollow Glen, an invented Pennsylvania community. The site brings cutting, welding, paint, final assembly, inspection, inventory, and administration together in one place. The fictional lineup grew to include enclosed cargo trailers in the 2000s and equipment trailers in the 2010s, alongside open utility trailers.</p>
      <p>Choosing a trailer starts with knowing the work it must do. Dealers can help discuss configurations, current availability, and the labels on a finished unit.</p>
      <p><a class="button" href="/trailers/index.html">View the trailers</a> <a class="button button-secondary" href="/dealers/index.html">How dealers help</a></p>
    </div>
    <div><img class="model-image" src="{FACTORY_IMAGE}" alt="Illustration of the fictional Laurel Run trailer manufacturing facility"></div>
  </div>
</section>''',
    },
    "resources/index.html": {
        "title": "Owner Resources | Laurel Run Trailer Works",
        "description": "Find fictional Laurel Run trailer care, warranty guidance, and dealer support resources in easy-to-read HTML pages.",
        "body": _hero("Helpful information", "Owner Resources") + '''<section class="section">
  <div class="container">
    <div class="article-body">
      <h2>Information for the road ahead</h2>
      <p>Start with these readable, printable guides for common trailer questions. They are general information for this fictional demonstration, not a substitute for a specific trailer's manual, labels, warranty documents, or applicable rules.</p>
    </div>
    <div class="resource-grid">
      <article class="info-card"><h3>Utility &amp; cargo brochure</h3><p>A printable introduction to the Trailfield and Enclosure models.</p><a class="text-link" href="/resources/utility-cargo-brochure.html">Open the brochure</a></article>
      <article class="info-card"><h3>Equipment trailer brochure</h3><p>A printable overview of the Workspan equipment trailer.</p><a class="text-link" href="/resources/equipment-brochure.html">Open the brochure</a></article>
      <article class="info-card"><h3>Warranty information</h3><p>Understand where to find the applicable documents and how a dealer can help with a question.</p><a class="text-link" href="/resources/warranty.html">Read warranty guidance</a></article>
      <article class="info-card"><h3>Trailer care and travel checklist</h3><p>Review a practical list for labels, tires, lights, brakes, loading, and maintenance.</p><a class="text-link" href="/resources/trailer-care.html">Open the care guide</a></article>
      <article class="info-card"><h3>Dealer support</h3><p>See the information a dealer may need to discuss a trailer, replacement parts, or a warranty question.</p><a class="text-link" href="/resources/dealer-support.html">Explore dealer support</a></article>
    </div>
    <div class="article-body">
      <h2>Frequently asked questions</h2>
      <div class="faq-list">
        <details><summary>Can I buy a trailer directly from the factory?</summary><p>No. In this fictional example, Laurel Run sells through independent dealers rather than directly to retail customers. Dealers set their own retail prices.</p></details>
        <details><summary>How do I find the carrying capacity?</summary><p>Read the certification and load labels on the completed trailer and account for installed equipment. An axle rating or nominal trailer dimension is not a payload rating.</p></details>
        <details><summary>Can I print these resources?</summary><p>Yes. These are ordinary HTML pages; use your browser's print command to keep a copy. No download or account is required.</p></details>
      </div>
      <p><a class="button" href="/trailers/index.html">Explore trailer models</a> <a class="button button-secondary" href="/dealers/index.html">Explore the dealer network</a></p>
    </div>
  </div>
</section>''',
    },
    "resources/warranty.html": {
        "title": "Warranty Information | Laurel Run Trailer Works",
        "description": "Learn how warranty questions are handled in the fictional Laurel Run example and why model-specific warranty documents govern coverage.",
        "body": _hero("Owner resources", "Warranty Information", (("Resources", "/resources/index.html"),)) + '''<section class="section">
  <div class="container article-body">
    <h2>Start with the documents for your trailer</h2>
    <p>Warranty coverage, if any, depends on the model and the applicable warranty documents supplied with a particular trailer. This overview does not state a warranty period, promise coverage, or replace those documents. Because this site is a fictional demonstration, no actual Laurel Run trailer or warranty is offered.</p>
    <h2>How a dealer can help</h2>
    <p>In the fictional dealer model, an independent dealer can help you find the relevant documents and understand how to raise a warranty question. Have the model, trailer identification details, purchase information, and a description of the concern ready for that discussion. Refer to the applicable documents for any process or information requirements.</p>
    <p class="notice">Do not post personal details or identification numbers in the demonstration confirmation form. The form prepares text locally and does not reach a dealer or the company.</p>
    <div class="faq-list">
      <details><summary>Is every repair covered?</summary><p>Coverage depends on the model and applicable warranty documents. This page does not establish coverage for any repair.</p></details>
      <details><summary>Who sets the warranty terms?</summary><p>Consult the warranty documents that apply to the specific trailer. This demonstration does not provide those terms.</p></details>
    </div>
    <p><a class="button" href="/resources/dealer-support.html">Dealer support</a> <a class="button button-secondary" href="/resources/index.html">All resources</a></p>
  </div>
</section>''',
    },
    "resources/trailer-care.html": {
        "title": "Trailer Care & Checklist | Laurel Run Trailer Works",
        "description": "Read a printable general trailer-care checklist covering labels, loading, connections, tires, lights, and maintenance.",
        "body": _hero("Owner resources", "Trailer Care & Checklist", (("Resources", "/resources/index.html"),)) + '''<section class="section">
  <div class="container article-body">
    <h2>A simple pre-trip check</h2>
    <p>Use this general checklist as a conversation starter, not as a complete inspection or a substitute for the finished trailer's manual, certification labels, tow-vehicle instructions, or local requirements. Print this page using your browser if a paper copy is useful.</p>
    <ol>
      <li><strong>Read the labels.</strong> Confirm the trailer's ratings and the limits of the tow vehicle, hitch, and other components. Do not assume payload from an axle rating or deck size.</li>
      <li><strong>Plan and secure the load.</strong> Check weight and distribution, secure items with appropriate equipment, and follow applicable cargo-securement rules. Close and secure gates, doors, and ramps.</li>
      <li><strong>Check the connection.</strong> Follow the instructions for the coupler, safety chains, electrical connection, and any breakaway system fitted to the trailer.</li>
      <li><strong>Inspect tires and wheels.</strong> Look for visible damage and check tire pressure and wheel-fastener requirements against the relevant labels and instructions.</li>
      <li><strong>Test lights and brakes.</strong> Confirm the lights and any trailer brakes operate properly before setting out. Address faults before travel.</li>
      <li><strong>Look over the trailer.</strong> Check the deck, frame, doors, ramps, and attachment points for damage or loose parts. Have concerns inspected by a qualified professional.</li>
    </ol>
    <h2>After the trip</h2>
    <p>Remove debris, note damage, and arrange service as directed by the trailer and component instructions. Maintenance needs vary with use, equipment, and conditions; use the intervals and procedures supplied for the specific unit.</p>
    <p><a class="button" href="/resources/dealer-support.html">Dealer support</a> <a class="button button-secondary" href="/resources/index.html">All resources</a></p>
  </div>
</section>''',
    },
    "resources/dealer-support.html": {
        "title": "Dealer Support | Laurel Run Trailer Works",
        "description": "Learn how the fictional Laurel Run independent dealer network can help with specifications, replacement parts, and warranty questions.",
        "body": _hero("Owner resources", "Dealer Support", (("Resources", "/resources/index.html"),)) + '''<section class="section">
  <div class="container article-body">
    <h2>Independent dealers are the starting point</h2>
    <p>In the Laurel Run demonstration, approximately 80 independent dealers work with the manufacturer. They handle retail sales and set their own retail prices. They can discuss trailer configurations, availability, delivery, replacement parts, and warranty questions for a specific unit. There are no actual Laurel Run dealers or products behind this fictional site.</p>
    <h2>Information to have ready</h2>
    <ul>
      <li>The model and the type of trailer, plus the configuration you are considering.</li>
      <li>The load, tow vehicle, and intended use, when discussing a purchase.</li>
      <li>The trailer identification details and a clear description of a parts or service question, if applicable.</li>
      <li>The applicable warranty documents when asking about warranty coverage.</li>
    </ul>
    <p>These are suggestions for a dealer conversation, not a claim that a particular part, service, or option is available. Check the completed unit's labels and instructions for its specifications and limitations.</p>
    <p class="notice">Please do not enter personal or trailer identification details in the demonstration confirmation form. It does not send a request to a dealer.</p>
    <p><a class="button" href="/dealers/index.html">Explore the dealer network</a> <a class="button button-secondary" href="/resources/warranty.html">Warranty guidance</a></p>
  </div>
</section>''',
    },
    "contact/index.html": {
        "title": "Contact & Owner Confirmation | Laurel Run Trailer Works",
        "description": "Prepare a local-only owner confirmation prompt for the fictional Laurel Run Trailer Works demonstration; no message is sent.",
        "body": _hero("Questions and confirmation", "Contact & Owner Confirmation") + '''<section class="section">
  <div class="container content-grid">
    <div class="article-body">
      <h2>Prepare a confirmation request</h2>
      <p>A visitor or industry-discovery agent can use this form to prepare a prompt asking an owner to confirm the company and its industry. This is a synthetic demonstration: the people and company are fictional, there is no messaging backend, and there is no real owner or dealer to receive the request.</p>
      <p>When the page's local script is available, the button prepares text for review on this page. It does not send an email, contact anyone, or store a submission. Do not enter sensitive or personal information. If the script is unavailable, no request is prepared or sent.</p>
      <p>For fictional product information, browse the <a class="text-link" href="/trailers/index.html">trailer lineup</a>, <a class="text-link" href="/resources/index.html">owner resources</a>, or <a class="text-link" href="/dealers/index.html">dealer network</a>.</p>
    </div>
    <div class="info-card">
      <h2>Request details</h2>
      <form id="owner-confirm-form" method="dialog" onsubmit="return false;">
        <div><label for="industry-name">Industry</label><input id="industry-name" type="text" value="Trailer manufacturing"></div>
        <div><label for="company-name">Company</label><input id="company-name" type="text" value="Laurel Run Trailer Works"></div>
        <div><label for="confirmation-question">Question for the owner</label><textarea id="confirmation-question" rows="6">Would you confirm whether Laurel Run Trailer Works manufactures trailers and explain how it works with independent dealers?</textarea></div>
        <button class="button" type="submit">Prepare confirmation request</button>
      </form>
      <div id="owner-confirm-result" aria-live="polite"></div>
      <p class="notice">Preparation only. Nothing is sent or stored by this site.</p>
    </div>
  </div>
</section>''',
    },
    "privacy/index.html": {
        "title": "Privacy | Laurel Run Trailer Works",
        "description": "Read the privacy notice for the fictional Laurel Run demonstration and its local-only confirmation form.",
        "body": _hero("Site information", "Privacy") + '''<section class="section">
  <div class="container article-body">
    <h2>A fictional, no-submission demonstration</h2>
    <p>Laurel Run Trailer Works, its people, dealers, and products are fictional. This site does not operate a real business or provide actual products or contact services.</p>
    <h2>Confirmation form</h2>
    <p>The owner-confirmation form is intended to prepare a draft in your browser. This site does not send or store form submissions, and the form does not contact an owner or dealer. Do not enter sensitive information or personal details. If the local script is unavailable, no draft is prepared.</p>
    <p>This notice concerns the demonstration site and its form; the service hosting the site or your browser may have its own technical practices.</p>
    <p><a class="text-link" href="/contact/index.html">View the confirmation form</a> · <a class="text-link" href="/terms/index.html">Read the site terms</a></p>
  </div>
</section>''',
    },
    "terms/index.html": {
        "title": "Terms of Use | Laurel Run Trailer Works",
        "description": "Read terms for the fictional Laurel Run demonstration, including its illustrative products, dealer information, and local-only form.",
        "body": _hero("Site information", "Terms of Use") + '''<section class="section">
  <div class="container article-body">
    <h2>Demonstration content</h2>
    <p>This website describes an invented company, people, dealers, and products. It is a fictional brochure demonstration, not an offer to sell trailers, arrange a purchase, provide a warranty, or contact an actual business or person.</p>
    <h2>Use of information</h2>
    <p>Product descriptions, illustrations, and general care guidance are illustrative and should not be relied on for a real purchase, inspection, towing decision, or warranty claim. For real equipment, use the manufacturer's instructions, completed-unit labels, applicable warranty documents, and relevant law; consult a qualified professional when needed.</p>
    <h2>Local-only confirmation form</h2>
    <p>The contact form may prepare a prompt for review in the browser. This site does not send or store submissions; it has no messaging backend. Do not enter personal or sensitive information, and do not treat a prepared prompt as a message sent or a confirmation received.</p>
    <p><a class="text-link" href="/privacy/index.html">Privacy notice</a> · <a class="text-link" href="/contact/index.html">Owner confirmation form</a></p>
  </div>
</section>''',
    },
}

PAGES.update({
    "contact/dealer.html": {
        "title": "Prepare a Dealer Inquiry | Laurel Run Trailer Works",
        "description": "Prepare a fictional dealer inquiry locally for the Laurel Run demonstration. No message is sent.",
        "body": _hero("Independent dealer inquiries", "Prepare a Dealer Inquiry", (("Dealers", "/dealers/index.html"),)) + '''<section class="section"><div class="container content-grid"><div class="article-body">
        <h2>Ask about a trailer</h2><p>In the Laurel Run scenario, independent dealers provide retail prices and discuss available configurations. The dealer names and states are fictional: there are no real dealers, addresses, or contact details behind this directory.</p>
        <p>Use this local-only form to prepare a sample inquiry for a test. No email is sent, no information is stored by the site, and no dealer will receive it. Do not enter personal or sensitive information.</p><p><a class="text-link" href="/dealers/index.html">Return to the dealer directory</a></p></div>
        <div class="info-card"><h2>Inquiry details</h2><form id="dealer-inquiry-form" method="dialog" onsubmit="return false;">
        <div class="field"><label for="inquiry-dealer">Fictional dealer name</label><input id="inquiry-dealer" type="text" placeholder="Choose a name from the directory"></div>
        <div class="field"><label for="inquiry-model">Trailer of interest</label><input id="inquiry-model" type="text" placeholder="For example, Trailfield"></div>
        <div class="field"><label for="inquiry-question">Question</label><textarea id="inquiry-question" rows="5">Could you tell me about available configurations and pricing?</textarea></div>
        <button class="button" type="submit">Prepare inquiry</button></form><div id="dealer-inquiry-result" aria-live="polite"></div><p class="notice">Simulation only. Nothing is sent or stored.</p></div></div></section>'''
    },
    "resources/utility-cargo-brochure.html": {
        "title": "Utility & Cargo Brochure | Laurel Run Trailer Works",
        "description": "A printable fictional product overview of Laurel Run utility and enclosed cargo trailers.",
        "body": _hero("Printable product overview", "Utility & Cargo Brochure", (("Resources", "/resources/index.html"),)) + '''<section class="section"><div class="container article-body">
        <h2>Two ways to carry the job</h2><p>Laurel Run builds open utility and enclosed cargo trailers for independent dealers. Use your browser's print command for a paper copy of this fictional overview.</p>
        <h3>Trailfield 6 × 12 open utility</h3><p>A steel open deck with a single electric-braked axle, rear loading gate, and lights. The nominal dimensions are a starting point; confirm the specific completed unit's label, usable load, and options.</p>
        <h3>Enclosure 7 × 14 cargo</h3><p>An enclosed tandem-axle trailer with a steel frame, aluminum exterior, plywood lining, rear door, and electric-braked axles. Interior space and usable load vary by configuration.</p>
        <h3>Choose with your dealer</h3><p>Discuss your load, tow vehicle, availability, and intended options with an independent dealer. Dealers set retail prices; the factory does not sell directly to retail customers. This brochure is a fictional demonstration, not an offer for an actual trailer.</p>
        <p><a class="button" href="/trailers/index.html">View the models</a> <a class="button button-secondary" href="/resources/index.html">All resources</a></p></div></section>'''
    },
    "resources/equipment-brochure.html": {
        "title": "Equipment Trailer Brochure | Laurel Run Trailer Works",
        "description": "A printable fictional product overview of the Laurel Run Workspan open equipment trailer.",
        "body": _hero("Printable product overview", "Equipment Trailer Brochure", (("Resources", "/resources/index.html"),)) + '''<section class="section"><div class="container article-body">
        <h2>Workspan: a wider deck</h2><p>With a nominal 82-inch-wide by 18-foot open steel deck, rear ramps, and tandem electric-braked axles, Workspan starts a conversation about carrying equipment. Each axle is rated at 5,200 pounds, which is a component rating and not the trailer's gross weight or payload rating.</p>
        <h3>Before choosing a configuration</h3><p>Consider equipment dimensions, weight, ground clearance, loading ramps, tie-downs, hitch, and tow-vehicle ratings together. Refer to the finished trailer's certification and load labels and the applicable instructions; do not infer payload by adding axle ratings.</p>
        <h3>Independent dealer support</h3><p>Independent dealers can discuss configuration, availability, and retail pricing. Laurel Run does not sell factory-direct to retail customers. This is a fictional overview, not an offer for an actual trailer. Use your browser's print command to keep a copy.</p>
        <p><a class="button" href="/trailers/workspan.html">Explore Workspan</a> <a class="button button-secondary" href="/resources/index.html">All resources</a></p></div></section>'''
    },
})
