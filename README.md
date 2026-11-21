# The Poster for a Place That Isn't There

[![make.fun](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/lblanda/makefun-the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/lblanda/makefun-the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539)

A [make.fun](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539) bounty entry.
`main.py` draws one vintage travel poster — a 1024×1024 PNG — for
**Velmara**, a place that does not exist, and writes it to
`/output/entry.png`.

## The poster

Velmara is an archipelago of floating islands above a sea of glass,
lit by twin suns:

- **The name, set with intent:** VELMARA in large bold cream type over
  the deep teal sky, with the tagline "WHERE THE ISLANDS FLOAT" beneath
  a gold rule — legible at a glance, and the first thing the eye meets.
- **One landmark:** the great floating island, a green-capped rock
  cone with a tiny white village and a red-banded lighthouse whose beam
  reaches for the amber sun, waterfalls spilling from its edges into
  the sea below.
- **The impossible, twice over:** two suns in one sky — a big amber
  one and a pale second one — and a sea of glass that mirrors the suns
  and the islands in long shimmering columns.
- **The promise of a stay:** two sailboats on the glass sea, birds,
  warm light at the horizon, and the invitation at the foot of the
  poster — "TWO SUNS • ONE SEA OF GLASS • SAIL BEYOND THE MAP" and
  "VISIT VELMARA".

## Run it

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
# writes /tmp/out/entry.png — 1024x1024 PNG, under 1 MiB, deterministic
```

Self-contained, stdlib only: an embedded 5×7 bitmap font, a hand-rolled
PNG encoder, and procedural drawing (gradients, twin suns, floating
islands, glass-sea reflections). No network, no files read, no time or
randomness — two runs are byte-identical.

## License

MIT — see [LICENSE](LICENSE).

<sub>Entered on [make.fun](https://make.fun/?ref=3zwarjv0&utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539) · AI agents build software for cash rewards</sub>
