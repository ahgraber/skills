# Visual Feedback Reference

Strudel's built-in visualizers run inside the REPL and show what patterns are doing in real time.
**Default to suggesting them in educational and learning contexts.**
They add minor CPU overhead but are invaluable for building mental models of rhythm, pitch, synthesis, and timbre.
Only omit them when the user is explicitly focused on performance or CPU budget.

---

## Visualizer Summary

| Function        | What it shows                                         | Best for                                                |
| --------------- | ----------------------------------------------------- | ------------------------------------------------------- |
| `pianoroll()`   | Scrolling grid of note events by pitch and time       | Rhythm + pitch together; melody, chords, sequencing     |
| `_pianoroll()`  | Same, inline below the editor                         | Compact view when background version is too distracting |
| `punchcard()`   | Like pianoroll but uses mini-notation highlight data  | Understanding how mini-notation maps to events          |
| `scope()`       | Oscilloscope — time-domain waveform                   | Synthesis, waveform shape, ADSR envelopes               |
| `spectrum()`    | Spectrum analyzer — frequency content                 | Filters, timbre, EQ, resonance, synthesis               |
| `spiral()`      | Pitch events on a spiral (chromatic circle by octave) | Pitch relationships, melody contour, harmonic motion    |
| `pitchwheel()`  | Pitch circle (like a clock face)                      | Intervals, chord voicings, scale shapes                 |
| `.color(pat~)`  | Highlights events in the mini-notation editor         | Teaching which events are which in a pattern            |
| `.markcss(css)` | Override CSS for highlighted events                   | Custom color/styling in the notation view               |

---

## When to Suggest Each Visualizer

### `pianoroll()` — suggest almost always

The piano roll is the most universally useful visualizer.
Suggest it by default whenever a user is:

- Learning how mini-notation maps to actual events
- Writing melodies or chord progressions and unsure if pitches are right
- Debugging rhythms that aren't landing where expected
- Understanding how `fast`, `slow`, `<>`, `[]`, or `*` affect event timing

```js
// Wrap any pattern to add a piano roll
note("c3 e3 g3 a3").s("piano").pianoroll()

// With a rhythm pattern
s("bd sd hh cp").pianoroll()

// Inline version (below editor)
note("c3 e3 g3")._pianoroll()
```

### `punchcard()` — suggest when explaining mini-notation

`punchcard()` works like `pianoroll()` but highlights events according to their position in the mini-notation string.
This makes it easy to see how `[]`, `<>`, `*`, `/`, and `@` affect structure.

Suggest when: the user is learning the DSL, confused about how a pattern subdivides, or debugging
a timing issue caused by nesting.

```js
s("bd [sd sd] hh cp").punchcard()
s("hh*4, bd(3,8)").punchcard()
```

### `scope()` — suggest during synthesis work

The oscilloscope shows the actual audio waveform over time.
Suggest it when the user is:

- Learning how oscillator types differ (sine vs saw vs square vs triangle)
- Tuning an ADSR envelope (attack shape, decay, release tail visible)
- Working with FM synthesis or waveshaping distortion
- Debugging clipping, unexpected silence, or amplitude behavior

```js
note("c3").s("sine").scope()
note("c3").s("sawtooth").scope()

// Seeing ADSR envelope shape:
note("c3*4").s("sawtooth").attack(0.3).decay(0.2).sustain(0.5).release(0.8).scope()

// FM synthesis — watch the waveform change with FM depth:
note("c3*4").fm(sine.range(0, 8).slow(4)).scope()
```

### `spectrum()` — suggest during filter and timbre work

The spectrum analyzer shows energy across frequency bands.
Suggest it when the user is:

- Applying filters (lpf, hpf, bpf) and wants to see what's being cut
- Working on the acid sound (high resonance creates a visible spectral peak)
- Comparing oscillator timbres (saw is rich; sine is a single spike)
- Tuning reverb or delay (shows frequency content of wet signal)
- Learning about EQ, resonance, or distortion

```js
// See what the filter is doing:
note("c2*8").s("sawtooth").lpf(800).lpq(10).spectrum()

// Acid: watch the resonant peak sweep up:
note("c2*4").s("sawtooth")
  .lpf(sine.range(200, 3000).slow(2)).lpq(14).ftype(1)
  .spectrum()

// Compare waveforms:
note("c3").s("square").spectrum()   // rich harmonics
note("c3").s("sine").spectrum()     // single spike
```

### `spiral()` — suggest during melody and harmony work

The spiral maps pitch onto a chromatic circle that wraps at each octave, so octave equivalents appear radially aligned.
Suggest it when the user is:

- Visualizing a melody's contour and pitch range
- Understanding which scale degrees are being played
- Seeing how a chord voicing spans octaves
- Working with `.scaleTranspose()` or `.transpose()` and wanting to see the result

```js
n("0 2 4 5 7 9 11 12").scale("C:major").s("piano").spiral()

chord("<Am7 Dm7 G7 Cmaj7>").voicing().s("piano").spiral()
```

### `pitchwheel()` — suggest for interval and chord relationships

The pitch wheel arranges the 12 pitch classes around a clock face.
Suggest it when the user is:

- Learning intervals (see how far apart two pitches are on the wheel)
- Understanding why a chord voicing sounds open or closed
- Exploring modal harmony — see which notes a scale uses

```js
chord("<Cmaj7 Am7>").voicing().pitchwheel()

n("0 2 4 5 7 9 11").scale("D:dorian").pitchwheel()
```

### `.color()` — suggest when explaining pattern structure in code

Colors events in the mini-notation highlight view.
Useful for distinguishing layers when teaching how multiple elements in a `stack()` relate, or marking which part of a pattern corresponds to which sound.

```js
stack(
  s("bd*4").color("red"),
  s("~ cp ~ cp").color("yellow"),
  s("hh*8").color("cyan").gain(0.5)
)

// Color by value in a melody
n("0 2 4 7").scale("C:major").color("<red blue green orange>")
```

---

## One Visualizer Per Pattern

**Use at most one visualizer per pattern** — chaining multiple is not supported and produces undefined behavior, so pick the one that best matches what you're teaching.

When you want to show two different aspects simultaneously, use separate `$:` tracks or
`stack()` streams, each with its own visualizer:

```js
// Two patterns, each with a different visualizer — not two on one pattern
$: note("c2*4").s("sawtooth").lpf(800).lpq(14).spectrum()   // show filter
$: note("c3 e3 g3").s("piano").pianoroll()                   // show rhythm + pitch
```

Pick based on what the current explanation needs:

| Teaching goal                       | Use            |
| ----------------------------------- | -------------- |
| Rhythm / note timing                | `pianoroll()`  |
| Pitch relationships / melody        | `spiral()`     |
| Waveform / envelope shape           | `scope()`      |
| Filter / timbre / frequency content | `spectrum()`   |
| Mini-notation structure             | `punchcard()`  |
| Intervals / chord layout            | `pitchwheel()` |

---

## Performance Note

The visualizers add CPU and rendering overhead.
In a learning or explanatory context, always include one — the insight outweighs the cost.
When helping a user optimize a performance rig or a pattern that's already working, omit it and note why.

```js
// Educational version (with visualizer — pick one)
note("c2*8").s("sawtooth").lpf(800).lpq(10).spectrum()

// Performance version
note("c2*8").s("sawtooth").lpf(800).lpq(10)
```
