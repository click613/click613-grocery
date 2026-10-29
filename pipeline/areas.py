"""Area list shared by the pipeline scripts. One row per public folder in ./site.
key = folder name under ./site (and under click613.com/grocery/), src = where that area's finished build lives in projects/."""
AREAS = [
    # key            name                          src (relative to projects/)                    old Tab address
    ("lakewood",     "Lakewood",                   "grocery-compare/site",                        "lakewoodprices"),
    ("bpflatbush",   "Boro Park & Flatbush",       "grocery-brooklyn/areas/bpflatbush/site",      "brooklynprices"),
    ("williamsburg", "Williamsburg",               "grocery-brooklyn/areas/williamsburg/site",    "williamsburgprices"),
    ("crownheights", "Crown Heights",              "grocery-brooklyn/areas/crownheights/site",    "crownheightsprices"),
    ("fivetowns",    "Five Towns",                 "grocery-fivetowns/site",                      "fivetownsprices"),
    ("monsey",       "Monsey",                     "grocery-monsey/site",                         "monseyprices"),
    ("kj",           "KJ / Monroe",                "grocery-kj/site",                             "kjprices"),
    ("teaneck",      "Teaneck / Bergenfield",      "grocery-teaneck/site",                        "teaneckprices"),
    ("passaic",      "Passaic / Clifton",          "grocery-passaic/site",                        "passaicprices"),
    ("queens",       "Queens (Kew Gardens Hills)", "grocery-queens/site",                         "queensprices"),
    ("farrockaway",  "Far Rockaway",               "grocery-farrockaway/site",                    "farrockawayprices"),
]
EXTRA = [
    # folder        src                               old Tab address
    ("",           "grocery-hub/site",              "click613grocery-hub"),    # the "pick your area" page = site root
    ("bot-api",    "grocery-bot-api/site",          "click613grocery-api"),    # static files of the WhatsApp-bot grocery API
]
STALE_HOURS = 48   # an area whose newest store read is older than this fails the run (alert)
