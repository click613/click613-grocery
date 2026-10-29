# Weekly flyer specials (Phase 2B)

Output: one JSON per store here (bingo.json, gourmetglatt.json, seasons-*-yossis.json).
Shape: {store, key, town, address, source, source_url, valid_from, valid_to, read_at, note, items:[{name, brand, size, price, price_text, deal}]}
price = per-item number ("2/$9" -> 4.5; "$7.49/lb" -> 7.49 with size "per lb").

## Weekly steps
1. `timeout -k 5 120 python3 refresh_flyers.py` -> writes todo.json: the newest Voice of Lakewood issue
   and the grocery-ad pages to read (text layer search, ~1 request + 1 JSON of ~400 KB, not saved).
2. Manual / vision step (prices are images; the text layer is scrambled):
   - For each ad page in todo.json: download files/pages/large/<n>.jpg (1811x2490) to /tmp,
     look at it in crops of ~600x950 px (attach_image), type the items, write <store>.json, DELETE the jpg.
   - Bingo: open https://www.bingowholesale.com/weeklydeals in the browser; the PDF viewer iframe loads a
     signed pdf.pdf-viewer-pro.com/....pdf (one tall page, 720 x ~6200 pt; prices are real PDF text,
     names are images). Render ONLY clipped strips with pymupdf (`clip=Rect(...)`, zoom 2) around each
     price row - rendering the whole page at zoom 2 (~55 MB bitmap) killed the kernel on this box.
     Dates are in the header ("Valid MM/DD/YY - MM/DD/YY"). Delete the PDF after.
3. Keep the dates printed in the ad; if none are printed, use the issue week and say so in "note".

## Known sources (Oct 16 2026)
- The Voice of Lakewood (weekly, Thursday): Gourmet Glatt 2-page ad (printed pp. 12-13) and Yossi's Cuts at Seasons (p. 25).
  No Bingo, KV Savings, Evergreen, NPGS or Aisle 9 grocery ads in issue 962.
- Bingo Wholesale: its own Weekly Deals flyer (Sunday-Saturday weeks), chain-wide.
- Lakewood Shopper: lakewoodshopper.com -> flipbookserver.com; server errors on Oct 16 2026, not read.
- KV Savings (605 E County Line Rd): no public flyer found online.
