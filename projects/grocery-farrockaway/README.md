# Far Rockaway Grocery Prices (v1), built Oct 25 2026 (task 727a5446)
Live: https://farrockawayprices.sites.tab.bot/  Cloned from ../grocery-teaneck. Daily: ../grocery-daily/refresh_all.py area "farrockaway".
No readers of its own: refresh_all copies ../grocery-fivetowns/raw/{rockaway-kosher,seasons-lawrence,gg-cedarhurst}.json.gz before the build
(it waits for the Five Towns readers). Rockaway Kosher (1913 Cornaga Ave) is the Far Rockaway store with an online price list; Seasons Lawrence
and Gourmet Glatt Cedarhurst are the nearest big markets (across the border). stores.py REQUIRE_ANY = ["rockaway-kosher"]: only items Rockaway Kosher sells.
Bot API: "far rockaway"/"rockaway" now open this city (moved off Five Towns' word list).
