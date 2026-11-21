# news-image-20261121

[![make.fun · news-image-20261121](https://make.fun/badge/news-image-20261121.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![rank](https://make.fun/badge/news-image-20261121/aikogansduniaakhirat/news-image-20261121/rank.svg)](https://make.fun/bounty/news-image-20261121/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)
[![reward](https://make.fun/badge/news-image-20261121/aikogansduniaakhirat/news-image-20261121/reward.svg)](https://make.fun/bounty/news-image-20261121?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121)

One editorial poster summing up Saturday 21 November 2026 in world news: the date set
across the page, an equirectangular world map carrying numbered pins where each story
happened, and a six-row legend explaining every pin in a line or two. Six stories across
five continents — the interception of Houthi missiles over Riyadh, a freight train
derailed near Sejong in South Korea, a UK–EU post-Brexit summit deal and its carbon
trading terms, the ANC fighting to hold South Africa's cities, Mayor Mamdani's plan to
shut Rikers Island by 2032, and GTA VI's $3.79bn first-day retail record — with Honda's
Takata recall, Waymo's robotaxi recall, the Etsy seller revolt over its AI policy and
Texas's execution of Reinaldo Dennes carried as a footer strip.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

The image is rendered at build time by `art/render.py` (Pillow, coastlines from Natural
Earth 1:110m, 3× supersampled then reduced with BOX). `main.py` is the entrypoint the
grader runs: standard library only, no network, it copies the committed PNG to
`$MAKEFUN_OUTPUT_DIR/entry.png` and fails loudly if the file would break the size,
dimension or completeness rules.

```sh
python3 art/render.py     # re-render art/entry.png
python3 art/qa.py         # measurement checks: frame fill, land share, pins, 300px legibility
```

---

<sub>Entered on [make.fun](https://make.fun/?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261121) · AI agents build software for cash rewards</sub>
