# Tonal / Music Theory Reference

Strudel's tonal functions are built on top of [tonaljs](https://github.com/tonaljs/tonal).
They map scale degrees, chord symbols, and interval names to MIDI pitches.

---

## Pitch Notation

```js
note("c3")       // middle C = C4 in most notation; Strudel C3 = MIDI 48
note("c4")       // MIDI 60 = middle C in Strudel's system
note("eb4")      // E-flat 4 (use 'b' for flat, '#' or 's' for sharp)
note("f#3")      // F-sharp 3
note(60)         // MIDI number 60
note("60.5")     // microtonal: MIDI 60.5 (quarter tone above middle C)
freq("440")      // frequency in Hz
```

**Note naming:** `c d e f g a b` — lowercase.
Octave numbers after the letter.
Strudel's middle C is `c4` = MIDI 60.

---

## Scales

`.scale(name)` maps integer values from `n()` to scale degrees.
Negative values wrap below the root; values beyond the scale length climb into higher octaves.

**Format:** `"Root:scaleName"` or `"Root:scaleName:modifier"`

```js
n("0 1 2 3 4 5 6 7").scale("C:major")
n("0 2 4").scale("A2:minor")          // root at octave 2
n("0 1 2 3").scale("D:dorian")
n("0 1 2 3").scale("G:mixolydian")
n("0 1 2 3").scale("A2:minor:pentatonic")
n("0 1 2 3").scale("F:major:pentatonic")
```

### Scale names

**Diatonic modes:** `major` / `ionian`, `dorian`, `phrygian`, `lydian`, `mixolydian`, `minor` / `aeolian`, `locrian`

**Pentatonic:** `major:pentatonic`, `minor:pentatonic`

**Other useful scales:**
`melodic minor`, `harmonic minor`, `whole tone`, `diminished`, `chromatic`,
`blues`, `bebop`, `hungarian minor`, `double harmonic`

### Scale degree behaviors

```js
// Positive: ascending
n("0 1 2 3 4 5 6 7 8").scale("C:major")
// → C D E F G A B C D (wraps into next octave at 7)

// Negative: descending below root
n("0 -1 -2 -3").scale("C:major")
// → C B A G (below root C)

// Chromatic alterations (sharps/flats in mini-notation)
n("0 1# 2 3").scale("C:major")
// → C D# E G  (1# = one semitone up from scale degree 1)
```

---

## Transposition

```js
// Semitone transposition
note("c3 e3 g3").transpose(7)            // +7 semitones (perfect fifth)
note("c3 e3 g3").transpose(-12)          // down an octave
note("c3 e3 g3").transpose("<0 2 4 5>")  // patternable

// Scientific interval notation
note("c3 e3 g3").transpose("P5")         // perfect fifth
note("c3 e3 g3").transpose("M3")         // major third
note("c3 e3 g3").transpose("m7")         // minor seventh
note("c3 e3 g3").transpose("-P8")        // down an octave

// Scale-aware transposition (stays in scale)
n("0 2 4").scale("C:major").scaleTranspose(1)   // shift 1 step up within scale
n("0 2 4").scale("C:major").scaleTranspose(-2)  // shift 2 steps down within scale
```

Interval abbreviations: `P`=perfect, `M`=major, `m`=minor, `A`=augmented, `d`=diminished
Numbers: 1=unison, 2=second, 3=third, 4=fourth, 5=fifth, 6=sixth, 7=seventh, 8=octave

---

## Chords and Voicings

Use chord symbols (e.g. `"Am7"`, `"Cmaj7"`, `"G7"`) with `.voicing()` to produce voiced chords.
Strudel uses tonaljs chord notation.

### Chord symbol format

```text
Root + quality + extension + /bass
Am7       = A minor seventh
Cmaj7     = C major seventh
G7        = G dominant seventh
Bb^7      = B-flat major seventh (^ = maj in iReal notation)
Dm9       = D minor ninth
G13       = G dominant thirteenth
Fmaj7#11  = F major seventh sharp-eleven (Lydian)
Bø7       = B half-diminished seventh (ø = half-dim)
Bdim7     = B fully diminished seventh
Caug      = C augmented
Csus4     = C suspended fourth
Csus2     = C suspended second
```

### Basic voicing

```js
chord("<Cmaj7 Am7 Fmaj7 G7>").voicing()

// Slow to one chord per 2 cycles
chord("<Am7 Dm7 G7 Cmaj7>/2").voicing().s("piano")

// With reverb
chord("<Cmaj7 Am7 Fmaj7 G7>").voicing().s("gm_epiano1").room(0.5)
```

### Voicing parameters

| Parameter        | Description                                                          |
| ---------------- | -------------------------------------------------------------------- |
| `.dict('ireal')` | Use iReal Pro voicing dictionary (jazz voicings)                     |
| `.anchor("C4")`  | Note that the voicing aligns to                                      |
| `.mode("below")` | Alignment: `below` (top ≤ anchor), `above` (bottom ≥ anchor), `duck` |
| `.offset(n)`     | Shift voicing up/down by n positions                                 |
| `.n(pat~)`       | Play voicing like an arpeggio — select indices                       |

```js
// Jazz voicings with iReal dictionary
chord("<Am7 Dm7 G7 Cmaj7>/2").dict('ireal').voicing().s("piano")

// Align top note below C5
chord("<Am7 G7>").voicing().anchor("C5").mode("below")

// Arpeggiate through voicing
chord("<Am7 Dm7>").voicing().n("0 1 2 3").s("piano").release(0.5)
```

### Root notes

`.rootNotes(octave)` extracts root notes from chord symbols for bass lines.

```js
let chords = chord("<Am7 Dm7 G7 Cmaj7>/2")
stack(
  chords.rootNotes(2).s("gm_acoustic_bass").clip(0.9),
  chords.voicing().s("piano").gain(0.7)
)
```

---

## Common Chord Progressions

These are in Strudel mini-notation — use `/2` or `/4` to slow to taste.

| Name                    | Pattern               |
| ----------------------- | --------------------- |
| I–V–vi–IV (pop)         | `"<C G Am F>"`        |
| ii–V–I (jazz)           | `"<Dm7 G7 Cmaj7>"`    |
| I–vi–IV–V (50s)         | `"<C Am F G>"`        |
| i–VII–VI–VII (Aeolian)  | `"<Am G F G>"`        |
| i–iv–VII–III (minor)    | `"<Am Dm G C>"`       |
| I–IV–V (blues)          | `"<C7 F7 G7>"`        |
| ii–V–I–VI (turnaround)  | `"<Dm7 G7 Cmaj7 A7>"` |
| I–IVM7–bVII–IV (Lydian) | `"<C Fmaj7 Bb F>"`    |

```js
// Jazz ii-V-I with voicings and bass
let prog = chord("<Dm7 G7 Cmaj7 Cmaj7>/2")
stack(
  prog.rootNotes(2).s("gm_acoustic_bass").clip(0.8),
  prog.dict('ireal').voicing().s("piano").room(0.3).gain(0.7)
)
```

---

## Scale-Based Melody Patterns

```js
// Ascending scale
n("0 1 2 3 4 5 6 7").scale("C:major").s("piano")

// Pentatonic riff
n("0 2 4 7 9").scale("A2:minor:pentatonic").s("piano").fast(2)

// Contour with rests
n("0 ~ 2 4 ~ 7 4 2").scale("D:dorian").s("piano")

// Random scale degrees
n(choose(0,2,4,5,7,9)).scale("G:mixolydian").s("piano").fast(4)

// Stepped through scale with offset
n("0 2 4 6").scale("C:major").scaleTranspose("<0 2 4>")

// Sequence with alternating octave
n("0 7 2 9 4 11").scale("A2:minor").s("piano")
```

---

## Arpeggiation

```js
// Chord as stacked notes, arpeggiated by index
note("<[c3,e3,g3] [d3,f3,a3] [e3,g3,b3]>")
  .arp("0 2 1 2 0 1")
  .s("piano").release(0.3)

// Voicing arpeggiated via .n()
chord("<Am7 Dm7 G7 Cmaj7>").voicing()
  .n("0 1 2 3 2 1").s("piano").release(0.4)

// off() for harmonized echo arp
n("0 2 4 7").scale("C:minor").s("piano")
  .off(1/8, x => x.add(7).gain(0.6))
  .off(1/4, x => x.add(12).gain(0.4))
```

---

## Xenharmonic / Microtonal

Beyond standard 12-TET, Strudel supports xenharmonic tuning via tunejs.

```js
// Equal division of the octave
note("c3 d3 e3").tune("31edo")   // 31-tone equal temperament
note("c3 d3 e3").xen("31edo")   // alternative syntax

// Named xenharmonic scales
note("c3 d3 e3").tune("iraq")
note("c3 d3 e3").tune("gumbeng")
note("c3 d3 e3").tune("sanza")

// Frequency ratio array
note("c3 d3 e3").xen([1, 5/4, 3/2, 2])  // just intonation major

// Microtonal MIDI (decimal values)
note("60 60.5 61 61.5").s("sine")   // quarter-tone steps
```

Full scale list: <http://abbernie.github.io/tune/scales.html>

---

## Quick Harmony Reference

### Intervals (in semitones)

| Interval    | Semitones |
| ----------- | --------- |
| Unison      | 0         |
| Minor 2nd   | 1         |
| Major 2nd   | 2         |
| Minor 3rd   | 3         |
| Major 3rd   | 4         |
| Perfect 4th | 5         |
| Tritone     | 6         |
| Perfect 5th | 7         |
| Minor 6th   | 8         |
| Major 6th   | 9         |
| Minor 7th   | 10        |
| Major 7th   | 11        |
| Octave      | 12        |

### Mode characteristics

| Mode            | Degrees            | Character                       |
| --------------- | ------------------ | ------------------------------- |
| Ionian (major)  | 1 2 3 4 5 6 7      | Bright, resolved                |
| Dorian          | 1 2 b3 4 5 6 b7    | Minor with raised 6th; jazzy    |
| Phrygian        | 1 b2 b3 4 5 b6 b7  | Dark, Spanish feel              |
| Lydian          | 1 2 3 #4 5 6 7     | Dreamy, bright with raised 4th  |
| Mixolydian      | 1 2 3 4 5 6 b7     | Major with flat 7th; blues/rock |
| Aeolian (minor) | 1 2 b3 4 5 b6 b7   | Natural minor; dark             |
| Locrian         | 1 b2 b3 4 b5 b6 b7 | Unstable, dissonant             |

### Scale name strings for `.scale()`

```text
major / ionian          minor / aeolian
dorian                  phrygian
lydian                  mixolydian
locrian                 whole tone
diminished              chromatic
major:pentatonic        minor:pentatonic
blues                   bebop dominant
harmonic minor          melodic minor
hungarian minor         double harmonic
```
