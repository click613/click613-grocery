#!/usr/bin/env python3
"""Click613 legal footer + Terms & Disclaimer page on a site dir. Idempotent; safe to re-run before every publish.
Usage: python3 add_disclaimer.py <site dir> <kind>   kind = prices | kosher | eruv | jobs | clubs
Adds (1) one always-visible footer line linking to disclaimer.html (inline-styled, no CSS file change) and
(2) disclaimer.html (copied from this folder). Paltiel (Click613) asked Oct 18 2026 3:10 AM."""
import sys, os, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
LINES = {
 "prices": "Prices are collected from public sources and may be wrong or out of date. Always confirm price, availability and kashrus in store. Click613 is not responsible for errors.",
 "kosher": "Prices and hechsher info are collected from public sources and may be wrong or out of date. Always check the hechsher on the package and ask your Rav. Click613 does not certify kashrus and is not responsible for errors.",
 "eruv": "Eruv boundaries are approximate and may be outdated, and an eruv can be down any week. Always check with the local eruv hotline or Rav before Shabbos. Not a halachic ruling. Click613 is not responsible for errors.",
 "jobs": "Listings come from employers and public posts; Click613 does not verify them and is not the employer or an agency. Confirm details directly. Click613 is not responsible for errors.",
 "clubs": "Club details come from organizers and public sources and may change. Always confirm with the club before you go. Click613 is not responsible for errors.",
}
def block(kind):
    return ('<p class="c613legal" style="margin:10px 0 6px;font-size:13px;line-height:1.45;color:inherit;opacity:.9">' + LINES[kind] +
            ' <a href="disclaimer.html" target="_blank" rel="noopener" style="color:inherit;font-weight:700;text-decoration:underline">Terms &amp; disclaimer</a></p>')
def apply(site, kind):
    I = os.path.join(site, "index.html"); h = open(I).read(); h0 = h
    h = re.sub(r'<footer class="c613legal-foot".*?</footer>\n?', '', h, flags=re.S)  # replace an older copy
    h = re.sub(r'\s*<p class="c613legal".*?</p>', '', h, flags=re.S)
    b = block(kind)
    h = re.sub(r'\s*<div class="c613legal-out".*?</div><!--/c613legal-->', '', h, flags=re.S)
    embed_hides_foot = any(".embed .foot{display:none}" in open(os.path.join(site, f), errors="ignore").read().replace(" .foot{", " .foot{")
                           or ".embed .top,.embed .foot{display:none}" in open(os.path.join(site, f), errors="ignore").read()
                           for f in os.listdir(site) if f.endswith(".css"))
    m = re.search(r'\n?(\s*)</div>\s*</footer>', h)
    if embed_hides_foot and '<footer class="foot">' in h:
        # the footer is hidden when the page is embedded (?embed=1), so the line sits just above it, visible in both views
        i = h.index('<footer class="foot">')
        h = (h[:i] + '<div class="c613legal-out" style="max-width:1100px;margin:16px auto 0;padding:0 16px">' + b +
             '<style>.embed .c613legal-out{padding-bottom:84px!important}</style></div><!--/c613legal-->\n' + h[i:])
    elif m:
        h = h[:m.start()] + "\n    " + b + h[m.start():]
    elif "</footer>" in h:
        i = h.rindex("</footer>"); h = h[:i] + "  " + b + "\n" + h[i:]
    else:
        i = h.rindex("</body>")
        h = h[:i] + '<footer class="c613legal-foot" style="max-width:1100px;margin:14px auto 18px;padding:0 12px">' + b + '</footer>\n' + h[i:]
    if h != h0: open(I, "w").write(h)
    shutil.copy(os.path.join(HERE, "disclaimer.html"), os.path.join(site, "disclaimer.html"))
    print("legal ok", kind, site)
if __name__ == "__main__":
    apply(sys.argv[1], sys.argv[2])
