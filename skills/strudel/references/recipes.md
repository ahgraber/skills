# Production Recipes

Ready-to-use patterns for common musical tasks.
All examples assume default tempo unless noted.
Set BPM with `setcpm(BPM / 4)` (for 4/4 time).

---

## Tempo Setup

```js
setcpm(120 / 4)   // 120 BPM
setcpm(124 / 4)   // deep house
setcpm(128 / 4)   // house
setcpm(132 / 4)   // house / techno
setcpm(135 / 4)   // techno
setcpm(140 / 4)   // techno / acid
setcpm(150 / 4)   // hard techno
setcpm(170 / 4)   // drum and bass
setcpm(174 / 4)   // drum and bass
setcpm(80 / 4)    // hip-hop / trap (at half-time feel)
setcpm(140 / 4)   // trap (double-time notation)
```

---

## Drum Patterns

### Four-on-the-floor (house/techno)

```js
stack(
  s("bd*4"),
  s("~ cp ~ cp"),
  s("hh*8").gain("[0.5 1]*4")
).bank("RolandTR909")
```

### Classic house

```js
stack(
  s("bd*4"),
  s("~ cp ~ cp"),
  s("oh*2, hh*4").gain("0.6 1 0.6 0.8"),
  s("hh*16").gain("[0.3 0.7]*8").swing(4)
).bank("RolandTR808")
```

### TR-909 techno

```js
stack(
  s("bd(3,8)"),
  s("~ sd ~ sd").gain(0.9),
  s("hh*16").gain("[0.4 0.8 0.6 1]*4"),
  s("oh(1,8,5)").gain(0.7)
).bank("RolandTR909")
```

### Euclidean polyrhythm drums

```js
stack(
  s("bd(3,8)"),
  s("sd(2,8,1)"),
  s("hh(5,8)").gain(0.5),
  s("oh(1,8,6)").gain(0.7),
  s("cp(2,8,4)").gain(0.6)
)
```

### Breakbeat / amen-style

```js
// Use a break sample, slice and rearrange
s("breaks165").loopAt(1)

// Slice and resequence
s("breaks165").slice(8, "0 1 2 3 4 5 6 7")

// Shuffle the slices
s("breaks165").splice(8, "0 2 1 3 4 6 5 7")
```

### Swing / groove

```js
// Add swing to 8th-note hi-hats
s("hh*8").swing(4)

// Manual swing: delay off-beats
s("hh*8").swingBy(1/8, 4)

// Groove via gain accents
s("hh*16").gain("[0.4 1 0.6 0.8 0.4 1 0.6 0.9]*2")
```

### 808 kick with pitch sweep

```js
s("bd*4").bank("RolandTR808")
  .penv(24).pdecay(0.4).pcurve(1).panchor(1)
  .gain(0.9)
```

### Trap hi-hats

```js
s("hh*16")
  .gain(rand.range(0.3, 1))
  .sometimes(x => x.ply(3))
  .bank("RolandTR808")
```

---

## Bass Lines

### Simple sub bass

```js
note("<c2 c2 eb2 f2>*4").s("sine")
  .decay(0.3).sustain(0).attack(0.005)
```

### Sawtooth synth bass

```js
note("<c2 c2 g1 bb1>*4").s("sawtooth")
  .lpf(400).lpq(4)
  .attack(0.01).decay(0.15).sustain(0.4).release(0.2)
```

### Acid bassline (303-style)

The acid sound comes from a resonant LP filter with a short envelope, played at varying pitches.

```js
note("<c2 c2 eb2 c2 f2 c2 g2 bb2>*2").s("sawtooth")
  .lpf(300).lpq(14).ftype(1)
  .lpenv(3500).lpa(0.005).lpd(0.12).lps(0.1).lpr(0.2)
  .attack(0.005).decay(0.1).sustain(0.6)
```

### Walking bass line from chord roots

```js
let chords = chord("<Am7 Dm7 G7 Cmaj7>/2")
chords.rootNotes(2).s("gm_acoustic_bass").clip(0.9)
```

### Funk bass (slap style)

```js
note("<c2 ~ eb2 ~ f2 ~ g2 ~>*2").s("gm_slap_bass_1")
  .clip("<0.1 0.5 0.1 0.8>")
  .gain(0.9)
```

---

## Melody Patterns

### Scale-based melody

```js
n("0 2 4 <0 6> 4 2 4 7").scale("A2:minor")
  .s("piano").slow(2).room(0.3)
```

### Pentatonic riff

```js
n("0 2 4 7 9 7 4 2").scale("A2:minor:pentatonic")
  .s("piano").fast(2)
```

### Melody with variation every 4 cycles

```js
n("0 2 4 5 4 2 0 ~").scale("C:major")
  .s("piano")
  .every(4, x => x.fast(2))
  .sometimes(x => x.add(7))
```

### Harmonized melody

```js
n("0 2 4 5").scale("C:major").s("piano")
  .superimpose(x => x.add(2).gain(0.6))   // add a third above
  .off(1/8, x => x.add(7).gain(0.4))      // delayed echo a fifth up
```

### Call-and-response with `<>`

```js
n("<0 2 4 5> <7 5 4 2>").scale("D:dorian")
  .s("piano").slow(2)
```

---

## Chord Patterns

### Sustained pad chords

```js
chord("<Cmaj7 Am7 Fmaj7 G7>/2")
  .voicing().s("gm_pad_new_age")
  .attack(0.5).sustain(0.9).release(1.5)
  .room(0.6).roomsize(4)
```

### Rhythmic chord stabs

```js
chord("<Am7 Dm7 G7 Cmaj7>")
  .voicing().s("gm_epiano1")
  .struct("x ~ x ~ ~ x ~ ~")
  .clip(0.3).gain(0.8).room(0.2)
```

### Piano with bass (full harmony)

```js
let chords = chord("<Am7 Dm9 G13 Cmaj7>/2")
stack(
  chords.rootNotes(2).s("gm_acoustic_bass").clip(0.8),
  chords.dict('ireal').voicing().s("piano").gain(0.7).room(0.3)
)
```

### Chord arpeggio

```js
chord("<Am7 Fmaj7 C G>").voicing()
  .n("0 1 2 3 2 1").s("piano")
  .release(0.4).room(0.3)
```

---

## Full Genre Templates

### House (124 BPM)

```js
setcpm(124 / 4)
stack(
  // Drums
  s("bd*4").bank("RolandTR909"),
  s("~ cp ~ cp").bank("RolandTR909").gain(0.85),
  s("oh*2, hh*4").bank("RolandTR909").gain(0.6).swing(4),

  // Chord stabs
  chord("<Am7 Dm9 G13 Cmaj7>/2")
    .dict('ireal').voicing().s("gm_epiano1")
    .struct("~ ~ x ~ ~ ~ x ~").clip(0.4)
    .room(0.4).gain(0.7),

  // Bass from chord roots
  chord("<Am7 Dm9 G13 Cmaj7>/2")
    .rootNotes(2).s("gm_slap_bass_1").clip(0.9)
)
```

### Techno (135 BPM)

```js
setcpm(135 / 4)
stack(
  // Four-on-the-floor with pitch sweep
  s("bd*4").bank("RolandTR909")
    .penv(-12).pdecay(0.2).pcurve(1),

  // Snare/clap
  s("~ cp ~ cp").bank("RolandTR909").gain(0.85),

  // 16th-note hats with velocity variation
  s("hh*16").bank("RolandTR909")
    .gain("[0.4 0.8 0.6 1]*4"),

  // Acid bassline
  note("<c1 c1 eb1 c1 f1 c1 g1 bb1>*2").s("sawtooth")
    .lpf(350).lpq(14).ftype(1)
    .lpenv(3000).lpa(0.005).lpd(0.1).lps(0.1),

  // Noise for air/texture
  s("white*16").gain(0.12)
    .decay(sine.fast(8).range(0.02, 0.1))
    .hpf(8000)
)
```

### Drum and Bass (174 BPM)

```js
setcpm(174 / 4)
stack(
  // Amen break at half-speed
  s("breaks165").loopAt(1).gain(0.9),

  // Sub bass (half-time, heavy)
  note("c1 ~ ~ c1 ~ ~ eb1 ~").s("sine")
    .attack(0.005).decay(0.5).sustain(0.2).release(0.1)
    .gain(1.1),

  // Additional texture hats
  s("hh*16").degrade().gain(0.35)
    .bank("RolandTR909")
)
```

### Trap (140 BPM, half-time feel)

```js
setcpm(140 / 4)
stack(
  // 808 kick (half-time: beats 1 and 3)
  s("bd").bank("RolandTR808")
    .penv(24).pdecay(0.6).pcurve(1).panchor(1)
    .struct("x ~ ~ ~ x ~ ~ ~ ~ ~ x ~ ~ ~ ~ ~"),

  // Snare on 2 and 4 (half-time)
  s("sd").bank("RolandTR808")
    .struct("~ ~ ~ ~ x ~ ~ ~ ~ ~ ~ ~ x ~ ~ ~"),

  // Rolling 16th hi-hats with dynamics
  s("hh*16").bank("RolandTR808")
    .gain(rand.range(0.2, 0.9))
    .sometimes(x => x.ply(3)),

  // Occasional open hat
  s("oh(1,8,5)").bank("RolandTR808").gain(0.7)
)
```

### Lo-fi Hip-Hop (80 BPM)

```js
setcpm(80 / 4)
stack(
  // Dusty drums
  s("bd sd bd sd").bank("AkaiLinn")
    .crush(10).room(0.2).gain(0.8),
  s("hh*8").gain("[0.3 0.6]*4").bank("AkaiLinn").swing(4),

  // Jazz chords
  chord("<Cmaj7 Am7 Dm7 G7>/2")
    .dict('ireal').voicing().s("piano")
    .room(0.5).crush(12).gain(0.6),

  // Bass
  chord("<Cmaj7 Am7 Dm7 G7>/2")
    .rootNotes(2).s("gm_acoustic_bass").clip(0.7).gain(0.8)
)
```

---

## Modulation and Automation Recipes

### Filter sweep with LFO

```js
// Slow filter open on a pad
note("c3,e3,g3").s("sawtooth")
  .lpf(sine.range(200, 4000).slow(8))
  .lpq(6)
  .room(0.4)
```

### Sidechain pump

```js
stack(
  s("bd*4").orbit(1),
  note("c3,e3,g3").s("sawtooth").orbit(2)
    .duckorbit(1).duckattack(0.15).duckdepth(0.9)
    .lpf(1200).room(0.4)
)
```

### Trance gate (gated chords)

```js
note("c3,e3,g3,b3").s("sawtooth")
  .tremolosync(0.125).tremolodepth(1).tremoloshape("square")
  .lpf(3000).room(0.5).gain(0.8)
```

### Pitch LFO / vibrato

```js
note("c4 d4 e4 g4").s("sawtooth")
  .vib(sine.range(3, 6).slow(4))
  .vibmod(0.4)
```

### Stereo width with jux

```js
// Wide stereo: reversed on right
n("0 2 4 6").scale("C:minor").s("piano").jux(rev)

// Harmonized stereo: fifth up on right
note("c3 e3 g3").s("piano")
  .juxBy(0.7, x => x.add(7).gain(0.7))
```

### Echo / delay feedback melody

```js
note("c3 ~ ~ e3 ~ ~ g3 ~").s("piano")
  .echo(4, 1/8, 0.5)
  .room(0.3)
```

---

## Song Structure Recipes

### Arrange: linear build

```js
setcpm(128 / 4)
const kick   = s("bd*4").bank("RolandTR909")
const hats   = s("hh*8").gain(0.5).bank("RolandTR909")
const snare  = s("~ cp ~ cp").bank("RolandTR909")
const bass   = note("<c2 c2 eb2 f2>*4").s("sawtooth").lpf(500).lpq(4)
const chords = chord("<Am7 Dm7 G7 Cmaj7>/2").voicing().s("gm_epiano1").room(0.4)

arrange(
  [4,  kick],
  [8,  stack(kick, hats)],
  [8,  stack(kick, hats, snare)],
  [16, stack(kick, hats, snare, bass)],
  [16, stack(kick, hats, snare, bass, chords)]
)
```

### every() for periodic variation

```js
stack(
  s("bd*4"),
  s("~ cp ~ cp"),
  s("hh*8").gain(0.5)
).bank("RolandTR909")
  .every(8, x => x.fast(2))          // double time every 8 cycles
  .every(16, x => stack(x, x.rev())) // layer reversed every 16
```

### chunk() for rotating fills

```js
// Apply a fill to successive parts of the beat
s("bd sd hh cp")
  .chunk(4, x => x.speed(2))         // each quarter gets doubled speed in turn
```

### someCycles() for live variation

```js
stack(
  s("bd*4"),
  s("~ cp ~ cp").someCycles(x => x.fast(2)),
  s("hh*8").someCycles(rev)
).bank("RolandTR909")
```

---

## Texture and Atmosphere

### Granular pad from sample

```js
s("pad").loop(1).loopBegin(0.1).loopEnd(0.9)
  .room(0.8).roomsize(6).gain(0.4)
  .lpf(sine.range(800, 3000).slow(12))
```

### Noise texture

```js
// High-frequency sizzle
s("white*16").gain(0.08).hpf(8000).decay(0.02)

// Ambient rumble
s("brown").gain(0.05).room(0.9).roomsize(8).gain(0.15)
```

### Layered drones

```js
stack(
  note("c2").s("sine").gain(0.3),
  note("c3").s("triangle").gain(0.2),
  note("g3").s("sine").gain(0.15).room(0.6),
  note("c4").s("triangle").gain(0.1).room(0.8)
)
```
