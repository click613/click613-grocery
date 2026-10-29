#!/usr/bin/env python3
"""Writes disclaimer.html (Click613 Terms & Disclaimer). Paltiel Oct 18 2026 3:10 AM: 'make sure I'm protected... no responsibility for any errors'; 3:12 AM: 'make sure stores can't sue for sharing their prices'.
Edit SECTIONS here, run it, then run add_disclaimer.py on each site dir."""
SECTIONS = [('Information only', ["Click613's websites, pages, maps, data feeds and WhatsApp bot answers (including the grocery price pages, the kosher alternatives page, the Eruvin 613 eruv map, the clubs and jobs pages, and the Click613 grocery data feed) are for general information only.", 'Everything is provided “as is” and “as available”, without warranties of any kind, express or implied. We do not guarantee that any information is accurate, complete, current or available at any given time, and we may change or remove anything at any time without notice.', 'You use this information at your own risk and are responsible for your own decisions.']), ('Prices', ["Prices are read from stores' public websites and apps, from printed store flyers, or estimated. Prices marked “approx.” are estimates made from Instacart prices with Instacart's markup removed; they are not the store's own prices.", 'Stores can change prices at any time. Sales may end early, be limited to certain stores, quantities or online orders, or need a minimum purchase. Items may be out of stock. Matching products between stores is done automatically and can be wrong.', "The price on the store's shelf or at the register always governs. Always confirm the price and availability with the store before you buy."]), ('Stores and brands', ["Prices and product details shown on our pages are factual information gathered from publicly available sources, such as stores' own public websites, apps and printed flyers, and are shown for comparison.", 'Store, chain and brand names, logos and trademarks belong to their owners and are used only to identify them.', 'Click613 is independent. It is not affiliated with, endorsed by, sponsored by, or speaking for any store, chain, brand, certifying agency or website named on our pages.', 'Any store or brand that wants its information corrected or removed can email <a href="mailto:admin@click613.com">admin@click613.com</a>, and we will handle it promptly.']), ('Kashrus', ["Click613 does not certify anything as kosher and does not give kashrus rulings. Hechsher information shown on our pages comes from the certifying agency's public lists and other public sources, and it can change or be wrong. Products, ingredients and certifications change without notice.", 'Always check the hechsher on the package itself, and ask your Rav about any kashrus question.']), ('Eruv map (Eruvin 613)', ['Eruv boundaries and pins are collected from community maps and other public sources. They are approximate, may be outdated, and may not show exclusions or recent changes. An eruv can be down in any given week.', "The map is not a halachic ruling and does not say whether any eruv is kosher or up. Always check with the local eruv's hotline or Rav before Shabbos, and ask your Rav about carrying."]), ('Jobs, clubs and other listings', ['Listings come from employers, organizers and public posts. Click613 does not check, verify or endorse them, and is not the employer, agency or organizer. Confirm all details directly with the person or business listed before you rely on them.']), ('Links to other sites and affiliate links', ['Our pages link to other websites and apps, such as Amazon, Costco, Walmart, Instacart and WhatsApp, and to store and organization websites. Those sites are run by others; their content, prices, products, privacy and terms are their responsibility, and your use of them is under their terms.', 'Some links may be affiliate links; Click613 may earn a small commission at no extra cost to you.']), ('No responsibility for errors; limitation of liability', ["Click613 is not responsible for errors, omissions or out-of-date information, or for any decision you make or anything you buy, do or don't do because of information on our pages, maps, data feeds or bot.", 'To the fullest extent permitted by law, Click613 and its owners, staff and partners are not liable for any loss, cost or damage of any kind, whether direct, indirect, incidental, special or consequential, arising from or related to using, or being unable to use, our sites, maps, data feeds or bot, or relying on any information in them. Where the law does not allow some of these limits, they apply to the fullest extent the law allows.']), ('Changes', ['We may update these terms and this disclaimer at any time by posting a new version here. By using our pages, maps, data feeds or bot, you agree to the version posted at that time.']), ('Corrections', ['Found a mistake? Please email <a href="mailto:admin@click613.com">admin@click613.com</a> and we\'ll look at it.'])]
UPDATED = 'October 18, 2026'
def page_html(back_href="./"):
    body=[]
    for h,ps in SECTIONS:
        body.append(f"<h2>{h}</h2>\n"+"\n".join(f"<p>{p}</p>" for p in ps))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Terms &amp; Disclaimer | Click613</title>
<meta name="description" content="Click613 terms and disclaimer: information only, no warranties, no responsibility for errors.">
<meta name="theme-color" content="#0B2A4A">
<style>
body{{margin:0;background:#F7F4EE;color:#1d2733;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Heebo,Arial,sans-serif}}
header{{background:#0B2A4A;color:#F7F4EE;border-bottom:4px solid #C9A227;padding:18px 18px 16px}}
header .brand{{font-weight:800;letter-spacing:.5px;font-size:15px;color:#F7F4EE;text-decoration:none}}
header .brand b{{color:#C9A227}}
header h1{{margin:6px 0 0;font-size:24px;line-height:1.25}}
main{{max-width:720px;margin:0 auto;padding:18px 18px 40px}}
.lead{{background:#fff;border-left:4px solid #0E6B3F;border-radius:8px;padding:12px 14px;margin:0 0 8px;font-weight:600}}
h2{{color:#0B2A4A;font-size:18px;margin:26px 0 6px;padding-bottom:4px;border-bottom:1px solid #e4dccb}}
p{{margin:0 0 10px}}
a{{color:#0E6B3F;font-weight:600}}
.updated{{color:#5b6470;font-size:14px;margin-top:28px}}
.back{{display:inline-block;margin-top:14px;background:#0E6B3F;color:#fff;text-decoration:none;padding:12px 18px;border-radius:10px}}
</style>
</head>
<body>
<header>
  <a class="brand" href="https://click613.com" target="_blank" rel="noopener">CLICK<b>613</b></a>
  <h1>Terms &amp; Disclaimer</h1>
</header>
<main>
<p class="lead">Click613's information is collected from public sources and may be wrong or out of date. Always confirm prices, availability and kashrus in the store, and eruv status with the local eruv, before you rely on it. Click613 is not responsible for errors.</p>
{chr(10).join(body)}
<p class="updated">Last updated {UPDATED}</p>
<a class="back" href="{back_href}">&larr; Back</a>
</main>
</body>
</html>
"""

if __name__ == '__main__':
    import os
    open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disclaimer.html'), 'w').write(page_html())
    print('ok')
