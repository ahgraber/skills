# Mini-Notation Reference

Mini-notation is Strudel's DSL for writing rhythmic and melodic patterns inside strings.
It is parsed inside `"double quotes"` (single-line) or `` `backticks` `` (multi-line).
Single quotes `'...'` are plain JavaScript — NOT parsed as mini-notation.

## Operator Table

| Syntax     | Name               | Description                                   | Example                         |
| ---------- | ------------------ | --------------------------------------------- | ------------------------------- |
| `a b c`    | Sequence           | Events share the cycle equally                | `"bd sd hh cp"`                 |
| `~` or `-` | Rest               | Silent step                                   | `"bd ~ sd ~"`                   |
| `[ ]`      | Sub-sequence       | Nested group; shares one step of outer cycle  | `"bd [sd sd] hh"`               |
| `< >`      | Alternate          | One element per cycle, rotates each cycle     | `"<c e g>"`                     |
| `,`        | Parallel / Stack   | Play all simultaneously                       | `"bd*2, hh*4"`                  |
| `*n`       | Speed up           | Repeat n times within its step                | `"hh*8"`                        |
| `/n`       | Slow down          | Stretch over n cycles                         | `"[c e g a]/4"`                 |
| `@n`       | Elongate (weight)  | Duration multiplier                           | `"c@3 e"` (c = 3× longer)       |
| `@` / `_`  | Elongate once      | Each adds one unit of weight                  | `"c @ @"` = `"c@3"`             |
| `!n`       | Replicate          | Repeat n times without speeding up            | `"c!3 e"` = `"c c c e"`         |
| `?`        | Random remove      | 50% chance of silence per event               | `"bd? sd"`                      |
| `?p`       | Weighted random    | p probability of keeping (0–1)                | `"bd?0.9"`                      |
| `\|`       | Random choice      | Pick one element randomly each cycle          | `"c\|e\|g"`                     |
| `(n,k)`    | Euclidean          | n beats spread over k steps (Bjorklund)       | `"bd(3,8)"`                     |
| `(n,k,r)`  | Euclidean + offset | Euclidean with rotation r                     | `"bd(3,8,1)"`                   |
| `:n`       | Sample index       | Select nth variant of a sample                | `"hh:3"`                        |
| `{ }%n`    | Polyrhythm         | Stepped sequence at n steps/cycle             | `"{a b c}%4"`                   |
| `.`        | Separator          | Divides sequence into equal parts (like `[]`) | `"1 2 . 3 . 4"` = `"[1 2] 3 4"` |
| `^`        | Step level         | Mark metrical level for stepwise functions    | `"a [^b c] d"`                  |
| `b`        | Flat               | Lower pitch by one semitone                   | `"eb3"`                         |
| `#` or `s` | Sharp              | Raise pitch by one semitone                   | `"f#3"` or `"fs3"`              |

## Key Rules and Mental Models

**Sequences share the cycle.**
`"bd sd hh cp"` = four equal quarter-note steps.
Adding `"bd sd hh cp oh"` gives five equal steps — each shorter, not the cycle longer.

**`<a b c>` is shorthand for `[a b c]/3`.**
One element per cycle; takes 3 cycles to complete.
Tempo is unaffected by how many elements you add.

**`[a b]` is a sub-sequence.**
It occupies one step of the outer pattern.
`"bd [sd sd] hh cp"` = 4 steps; the second step subdivides into two fast snares.

**`*` and `/` accept decimals.** `"hh*2.5"`, `"[a b]/1.5"`.

**`,` inside `[]` creates chords.** `"[c,e,g] [d,f]"` plays two chords in sequence.

## Examples by Concept

### Basic sequences

```js
s("bd sd hh cp")               // 4-step sequence
s("bd [sd sd] hh cp")          // snare subdivided into 2
s("bd [hh hh hh] sd hh")       // triplet subdivision
```

### Alternation (one per cycle)

```js
s("<bd sd>")                   // kick one cycle, snare the next
note("<c3 e3 g3>")             // cycles through c, e, g
note("<[c3,e3] [d3,f3]>")      // alternates between two chords
```

### Speed and stretch

```js
s("hh*8")                      // 8 hi-hats per cycle
s("hh*16").gain(0.5)           // 16th-note hats
s("[bd sd]/2")                 // one kick-snare pair over 2 cycles
note("[c3 e3 g3 a3]/2")        // melody over 2 cycles
```

### Elongation and weight

```js
s("bd@3 sd")                   // kick = 75%, snare = 25%
s("bd _ _ sd")                 // same as bd@3 sd
s("c@2 e g@2 a")               // c and g twice as long as e and a
```

### Rests

```js
s("bd ~ sd ~")                 // classic backbeat
s("bd ~ ~ sd ~ ~ bd sd")       // displaced pattern
```

### Euclidean rhythms

Euclidean rhythms distribute n beats as evenly as possible over k steps.
Many standard rhythms are Euclidean:

```js
s("bd(3,8)")     // "pop clave" / tresillo — archetypal Latin rhythm
s("sd(2,8,1)")   // snare on offbeats
s("hh(5,8)")     // quintuplet feel
s("oh(1,8,6)")   // single open hat accent
s("cp(3,8,2)")   // clap variant with offset
```

Common Euclidean patterns:

| Pattern   | Name             |
| --------- | ---------------- |
| `(2,3)`   | Tresillo base    |
| `(3,8)`   | Tresillo / clave |
| `(3,4)`   | Waltz            |
| `(4,12)`  | Fandango         |
| `(5,8)`   | Quintuplet clave |
| `(5,16)`  | Bossa nova       |
| `(7,8)`   | Aksak            |
| `(7,12)`  | Bulgarian 7      |
| `(7,16)`  | Samba            |
| `(9,16)`  | Son              |
| `(11,24)` | Adana / 11/24    |

### Random

```js
s("hh? sd")                    // 50% chance hh plays
s("hh?0.8 sd")                 // 80% chance hh plays
s("bd|sd|hh")                  // one picked randomly each cycle
s("bd*8").degrade()            // randomly remove ~50% at runtime
```

### Polyrhythm / polymeters

```js
// Comma inside pattern: simultaneous streams
s("bd*4, ~ cp ~ cp, hh*8")

// Polyrhythm via {}: align by step count, not cycle
s("{bd sd hh}%4")              // 3-step pattern at 4 steps/cycle

// Alternating structure
note("<[c,e,g] [d,f,a] [e,g,b]>").s("piano")
```

### Sample index

```js
s("hh:0 hh:1 hh:2 hh:3")      // four hi-hat variants in sequence
n("0 1 2 3").s("hh")           // equivalent using n()
s("<hh:0 hh:2>*4")             // alternate between two hats
```

### Chaining operators

Operators compose naturally:

```js
s("bd(3,8)*2")                 // euclidean, doubled
s("[bd sd]*2")                 // sub-sequence, doubled
s("<bd hh>*4")                 // alternate at 4× speed
s("hh!4?")                     // four hats, each 50% chance
s("bd _ [sd sd] ~")            // elongation + subdivision + rest
```

## Parameter Shorthand

Some effect methods accept `:` to separate related parameters inline:

```js
.lpf("800:5")        // lpf=800, lpq=5 (freq:resonance)
.delay("0.5:0.25:0.4")  // delay:delaytime:delayfeedback
.room("0.5:2")       // room:roomsize
.adsr(".01:.1:.5:.2") // attack:decay:sustain:release
```
