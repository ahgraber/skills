# Attributions and citations

The AI-tells catalog is adapted and de-duplicated from two sources:

- Wikipedia's [_Signs of AI writing_](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing), maintained by WikiProject AI Cleanup — a field guide drawn from thousands of observed instances of AI-generated text.
- [tropes.fyi](https://tropes.fyi)'s tropes catalog, originally published by [tropes.fyi](https://tropes.fyi/tropes-md) and attributed to [ossama.is](https://ossama.is).

Lineage and background:

- The "de-slop" framing is in the spirit of [blader/humanizer](https://github.com/blader/humanizer), a Claude Code skill for removing signs of AI-generated writing.
- Packaging The Economist's guide as an editing skill follows [TAJD/economist-style-guide-plugin](https://github.com/TAJD/economist-style-guide-plugin) (Tom Dickson).
- The surface-tic vs. structural-reflex split reflects empirical detection work — notably Kobak, González-Márquez, Horvát & Lause, _"Delving into LLM-assisted writing in biomedical publications through excess vocabulary,"_ Science Advances (2025), arXiv:2406.07016 — which finds the LLM fingerprint is a style-word shift rather than a content shift.

Prose-craft directives draw on the standard style canon:

- Strunk, William.
  _The Elements of Style._
  Project Gutenberg, 2011, eBook no. 37134, <https://www.gutenberg.org/ebooks/37134>.
- Williams, Joseph M., and Joseph Bizup.
  _Style: Lessons in Clarity and Grace_ — for the cohesion (local flow) vs. coherence (global structure) distinction.
- Pinker, Steven.
  _The Sense of Style_ — for arcs of coherence and classic style.
- Orwell, George.
  _Politics and the English Language_ (1946) — for the rule against figures of speech you are used to seeing in print.
- _The Economist Style Guide_ — for the tone "do nots" (stuffy, hectoring, self-satisfied, chatty, didactic), the neutral-reporting-verb rulings, the rule that spelling dialect and date conventions follow the document, and the paired warning against timid and arrogant confidence.

Register modules:

- The genre-by-formality model draws on Joos, Martin.
  _The Five Clocks_ (1961) and Biber's multi-dimensional register analysis.
- The technical register's four modes follow [Diátaxis](https://diataxis.fr) (Daniele Procida).
- The instructional-passage rules follow [ASD-STE100 Simplified Technical English](https://asd-ste100.org) (AeroSpace and Defence Industries Association of Europe).
- Reading STE as guidance for LLM-generated prose follows [AminBlg/SimpleEnglish](https://github.com/AminBlg/SimpleEnglish).

The target passages in `references/exemplars.md` are quoted, with light mechanical normalization, from the skill author's blog, [AI/MLbling About](https://aimlbling-about.ninerealmlabs.com/) — specifically from the posts _Pushing Back Against Cognitive Surrender_, _Stop Sloppypasta_, _How I Use AI (Apr, 2026)_, _Predicting LLM Parameters Using Benchmarks_, _MAIM Is MADness_, and _Sycophancy, Planning, and the Pepsi Challenge_.
The near-miss and tell counterparts in that file are synthetic.
