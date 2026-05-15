# Pattern Functions Reference

All functions are chainable methods unless noted as standalone constructors.
Parameters that accept patterns are marked with `~` — they can take mini-notation strings or other patterns.

---

## Pattern Constructors

Standalone functions that create patterns.

| Function                   | Mini equiv       | Description                                                                |
| -------------------------- | ---------------- | -------------------------------------------------------------------------- |
| `cat(a, b, c)`             | `"<a b c>"`      | Concatenate: each item takes one full cycle. Aliases: `slowcat`            |
| `seq(a, b, c)`             | `"a b c"`        | Sequence: all items crammed into one cycle. Aliases: `fastcat`, `sequence` |
| `stack(a, b, c)`           | `"a,b,c"`        | Play simultaneously                                                        |
| `stepcat([3,a],[2,b])`     | `"a@3 b@2"`      | Proportional concatenation by step count. Aliases: `timeCat`, `timecat`    |
| `arrange([n, pat], ...)`   | —                | Sequence patterns over explicit cycle counts                               |
| `polymeter([a,b,c],[x,y])` | `"{a b c, x y}"` | Align by step count across patterns. Alias: `pm`                           |
| `polymeterSteps(n, pats)`  | `"{...}%n"`      | Force n steps/cycle                                                        |
| `silence`                  | `"~"`            | Empty pattern                                                              |
| `run(n)`                   | —                | Integers 0 to n−1 as a sequence                                            |
| `binary(n)`                | —                | Integer → binary event pattern                                             |
| `binaryN(n, bits)`         | —                | Binary, padded to `bits` length                                            |

```js
// arrange: build song structure from sections
arrange(
  [4, s("bd*4")],                           // 4 cycles of kick
  [8, stack(s("bd*4"), s("hh*8"))],          // 8 cycles of kick + hats
  [4, stack(s("bd*4"), note("c3 e3").s("piano"))]
)

// polymeter: 3-step and 2-step patterns drifting against each other
polymeter(seq("a","b","c"), seq("x","y"))
```

---

## Time Modifiers

| Function                  | Mini equiv | Aliases    | Description                                          |
| ------------------------- | ---------- | ---------- | ---------------------------------------------------- |
| `.fast(n~)`               | `*n`       | `density`  | Speed up by factor n                                 |
| `.slow(n~)`               | `/n`       | `sparsity` | Slow down by factor n                                |
| `.early(n~)`              | —          | —          | Nudge earlier by n cycles                            |
| `.late(n~)`               | —          | —          | Nudge later by n cycles                              |
| `.rev()`                  | —          | —          | Reverse events within each cycle                     |
| `.palindrome()`           | —          | —          | Alternate forward/backward each cycle                |
| `.iter(n)`                | —          | —          | Rotate start point each cycle; completes in n cycles |
| `.iterBack(n)`            | —          | `iterback` | Like `iter`, reversed                                |
| `.ply(n~)`                | —          | —          | Repeat each event n times                            |
| `.segment(n~)`            | —          | `seg`      | Discretize a continuous signal at n events/cycle     |
| `.compress(a, b)`         | —          | —          | Compress cycle into time span [a,b]; leaves gap      |
| `.zoom(a, b)`             | —          | —          | Play only portion [a,b] of each cycle                |
| `.linger(f)`              | —          | —          | Repeat fraction f to fill the cycle                  |
| `.fastGap(n)`             | —          | `fastgap`  | Speed up but leave gap for remainder                 |
| `.inside(n, fn)`          | —          | —          | Apply fn inside n cycles                             |
| `.outside(n, fn)`         | —          | —          | Apply fn outside n cycles                            |
| `.ribbon(offset, cycles)` | —          | `rib`      | Loop a slice of the timeline                         |
| `.swingBy(x, n)`          | —          | —          | Delay second half of each n-division by x            |
| `.swing(n)`               | —          | —          | `swingBy(1/3, n)`                                    |
| `.cpm(n)`                 | —          | —          | Local cycles-per-minute override                     |

```js
note("c3 e3 g3").fast(2)           // double speed
note("c3 e3 g3").slow(2)           // half speed (over 2 cycles)
note("c3 e3 g3").early(0.25)       // shift 1/4 cycle earlier
note("c3 e3 g3").iter(4)           // rotates start point over 4 cycles
note("c3 e3 g3").rev()             // g3 e3 c3
note("c3 e3 g3").ply(2)            // c3 c3 e3 e3 g3 g3
s("hh*8").swing(4)                 // swing 8th notes
```

---

## Conditional Modifiers

Apply transformations based on cycle position or a pattern.

| Function            | Aliases     | Description                                                   |
| ------------------- | ----------- | ------------------------------------------------------------- |
| `.every(n, fn)`     | —           | Apply fn every n cycles (on the nth)                          |
| `.firstOf(n, fn)`   | —           | Apply fn on first cycle of every n                            |
| `.lastOf(n, fn)`    | —           | Apply fn on last cycle of every n                             |
| `.when(pat~, fn)`   | —           | Apply fn when binary pattern is 1                             |
| `.chunk(n, fn)`     | `slowChunk` | Divide into n parts; apply fn to one part per cycle, rotating |
| `.chunkBack(n, fn)` | `chunkback` | Like `chunk`, reversed                                        |
| `.struct(pat~)`     | —           | Apply the rhythmic structure of pat to this pattern           |
| `.mask(pat~)`       | —           | Silence events where pat is 0 or `~`                          |
| `.reset(pat~)`      | —           | Reset to cycle start on each onset of pat                     |
| `.restart(pat~)`    | —           | Restart from cycle 0 on each onset of pat                     |
| `.hush()`           | —           | Silence this pattern                                          |
| `.invert()`         | `inv`       | Swap 0s and 1s in a binary pattern                            |

```js
// Apply variation every 4th cycle
s("bd sd hh cp").every(4, x => x.fast(2))

// Apply fn when binary pattern is 1
note("c3 e3 g3").when("<0 0 1 0>", x => x.add(12))

// Rotate through a transformation chunk by chunk
note("c3 d3 e3 f3").chunk(4, x => x.add(7))

// Use one pattern's rhythm to gate another
note("c3 e3 g3").struct("x ~ x x ~ x ~ ~")

// Silence when mask is 0
s("hh*8").mask("1 0 1 1 0 1 0 1")
```

---

## Random Modifiers

All randomness in Strudel is _deterministic by seed_ — the same pattern plays the same random choices on every run.

| Function                    | Aliases    | Description                                           |
| --------------------------- | ---------- | ----------------------------------------------------- |
| `.degrade()`                | —          | Remove ~50% of events randomly                        |
| `.degradeBy(p~)`            | —          | Remove events with probability p (0–1)                |
| `.undegradeBy(p~)`          | —          | Inverse: keep events with probability p               |
| `.sometimes(fn)`            | —          | Apply fn ~50% of the time per event                   |
| `.sometimesBy(p~, fn)`      | —          | Apply fn with probability p                           |
| `.often(fn)`                | —          | `sometimesBy(0.75, fn)`                               |
| `.rarely(fn)`               | —          | `sometimesBy(0.25, fn)`                               |
| `.almostAlways(fn)`         | —          | `sometimesBy(0.9, fn)`                                |
| `.almostNever(fn)`          | —          | `sometimesBy(0.1, fn)`                                |
| `.someCycles(fn)`           | —          | Apply fn to ~50% of cycles (whole cycles, not events) |
| `.someCyclesBy(p~, fn)`     | —          | Apply fn to cycles with probability p                 |
| `choose(a, b, c)`           | —          | Constructor: randomly pick one value per event        |
| `wchoose([v,w], ...)`       | —          | Weighted random pick: `[value, weight]` pairs         |
| `chooseCycles(a, b, c)`     | `randcat`  | Pick one per cycle                                    |
| `wchooseCycles([v,w], ...)` | `wrandcat` | Weighted per-cycle pick                               |

```js
s("hh*8").degrade()                        // sparse hats
s("hh*8").degradeBy(0.3)                   // remove 30%
s("bd sd hh").sometimes(x => x.room(0.5))  // random reverb
s("bd sd hh").rarely(x => x.speed(2))      // rarely pitch-shifted
s("bd sd hh").someCycles(x => x.rev())     // whole cycles reversed randomly
n(choose(0,2,4,7)).scale("C:minor")        // random scale degree
```

---

## Accumulation / Layering

Layer and offset copies of a pattern.

| Function                         | Aliases    | Description                                                  |
| -------------------------------- | ---------- | ------------------------------------------------------------ |
| `.superimpose(fn)`               | —          | Layer fn(pattern) over the original (original kept)          |
| `.layer(fn1, fn2, ...)`          | —          | Layer fn results (original NOT kept)                         |
| `.off(time~, fn)`                | —          | Superimpose fn result delayed by time (in cycles)            |
| `.echo(times, time~, feedback~)` | —          | Stutter: times copies, each offset by time, gain × feedback  |
| `.echoWith(times, time~, fn)`    | `stutWith` | Like `echo` but applies fn each iteration                    |
| `.jux(fn)`                       | —          | Apply fn to right channel; original on left (instant stereo) |
| `.juxBy(amt~, fn)`               | `juxby`    | Like `jux` with stereo width 0–1                             |

```js
// Superimpose a harmony a fifth above
note("c3 e3 g3").superimpose(x => x.add(7).gain(0.7))

// Layer two transformed versions (no original)
note("c3 e3 g3").layer(
  x => x.speed(0.5),
  x => x.add(12)
)

// Echo: 3 copies, 1/8 cycle apart, 60% feedback
note("c3 e3 g3").echo(3, 1/8, 0.6)

// Delay a harmonized copy
note("c3 e3 g3").off(1/8, x => x.add(7).gain(0.6))

// Stereo: reversed right channel
note("c3 d3 e3 f3").jux(rev)

// Slightly wider stereo
note("c3 d3 e3 f3").jux(x => x.add(2).gain(0.8))
```

---

## Selection / Structural

Pick from lists, inhabit patterns, and arpeggiate chords.

| Function               | Aliases       | Description                                                   |
| ---------------------- | ------------- | ------------------------------------------------------------- |
| `.arp(pat~)`           | —             | Select note indices from a stacked chord                      |
| `.arpWith(pat~, fn)`   | —             | Select indices and apply fn to each                           |
| `.pick(pat~, list)`    | —             | Pick from list by index; maintains structure of list patterns |
| `.pickmod(pat~, list)` | —             | Like `pick`, wraps index around list length                   |
| `.inhabit(pat~, list)` | `pickSqueeze` | Like `pick` but squeezes cycle into step duration             |
| `.squeeze(pat~, list)` | —             | Compress selected pattern into selecting event's duration     |

```js
// Arpeggiate a chord
note("<[c3,e3,g3] [d3,f3,a3]>").arp("0 2 1 2")

// Pick from a list of patterns by index pattern
pick("<0 1 2>", [s("bd"), s("sd"), s("hh")])
```

---

## Arithmetic

Apply math to note values, indices, or any numeric parameter.

| Method     | Tidal equiv | Description |
| ---------- | ----------- | ----------- |
| `.add(n~)` | \`          | + n\`       |
| `.sub(n~)` | \`          | - n\`       |
| `.mul(n~)` | \`          | \* n\`      |
| `.div(n~)` | \`          | / n\`       |
| `.mod(n~)` | \`          | % n\`       |
| `.set(n~)` | \`          | < n\`       |

Each has directional variants: `.add.in(n)`, `.add.out(n)`, `.add.mix(n)`.

```js
note("0 2 4 6").scale("C:minor").add("<0 2 4>")  // transposing melody
note("c3 e3 g3").mul(sine.range(0.9, 1.1).slow(4)) // vibrato-like
```

---

## Continuous Signals

Signals are patterns with infinite temporal resolution — use them for LFO-style modulation.
They oscillate over one cycle by default; use `.slow()` / `.fast()` to control rate.

| Signal              | Range  | Description                       |
| ------------------- | ------ | --------------------------------- |
| `sine`              | 0–1    | Sine wave                         |
| `cosine`            | 0–1    | Cosine wave                       |
| `saw`               | 0–1    | Sawtooth wave                     |
| `tri`               | 0–1    | Triangle wave                     |
| `square`            | 0–1    | Square wave                       |
| `rand`              | 0–1    | Continuous random (smooth)        |
| `perlin`            | 0–1    | Perlin noise (smoother than rand) |
| `irand(n)`          | 0–n−1  | Random integers                   |
| `brand`             | 0 or 1 | Binary random                     |
| `brandBy(p)`        | 0 or 1 | Binary random with probability p  |
| `mouseX` / `mouseY` | 0–1    | Mouse position (interactive)      |

**`2` variants** (`sine2`, `saw2`, `rand2`, etc.) oscillate **−1 to 1**.

Signal methods:

- `.range(min, max)` — rescale output to [min, max]
- `.slow(n)` / `.fast(n)` — one full oscillation per n cycles / n per cycle
- `.segment(n)` — discretize to n steps per cycle

```js
// LFO on filter cutoff
note("c2*8").s("sawtooth")
  .lpf(sine.range(200, 4000).slow(8))
  .lpq(8)

// Random gain per event
s("hh*16").gain(rand.range(0.4, 1))

// Smooth pitch vibrato
note("c3").vib(sine.range(3, 6).slow(4))

// Perlin noise for organic feel
s("hh*8").gain(perlin.range(0.3, 1).slow(2))

// Patterned LFO speed
note("c3").s("sawtooth")
  .lpf(sine.range(100, 2000).slow("<4 2 8 1>"))
```

---

## Stepwise (Experimental)

Stepwise functions operate on a count of discrete steps per cycle rather than on continuous time.
Useful for building sequencer-style patterns.

| Function             | Aliases | Description                            |
| -------------------- | ------- | -------------------------------------- |
| `.pace(n)`           | —       | Fit pattern to n steps/cycle           |
| `.expand(n)`         | —       | Expand step size by factor n           |
| `.contract(n)`       | —       | Contract step size by factor n         |
| `.extend(n)`         | —       | Like `fast` but increases step count   |
| `.take(n)`           | —       | Take first n steps (negative = last n) |
| `.drop(n)`           | —       | Drop first n steps                     |
| `polymeter(...pats)` | `pm`    | Align steps across patterns            |
| `.shrink(n)`         | —       | Progressively shrink by n steps        |
| `.grow(n)`           | —       | Progressively grow by n steps          |
| `zip(...pats)`       | —       | Zip steps of patterns together         |

---

## Global Utilities

| Function                 | Description                                                        |
| ------------------------ | ------------------------------------------------------------------ |
| `setcpm(n)`              | Set global cycles per minute (`setcpm(120/4)` = 120 BPM in 4/4)    |
| `setCps(n)`              | Set global cycles per second (`setCps(140/60/4)` = 140 BPM in 4/4) |
| `all(fn)`                | Apply fn to all currently running patterns                         |
| `hush()`                 | Stop all patterns                                                  |
| `silence`                | Empty pattern (standalone)                                         |
| `register(name, fn)`     | Register a custom chainable method                                 |
| `createParams(...names)` | Create custom control parameters                                   |
