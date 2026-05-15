# Audio Effects Reference

All effect parameters are chainable methods and accept mini-notation strings or signals for modulation.

## Signal Chain Order

Events flow through this chain in order:

```text
gain + amplitude ADSR
  → lpf → hpf → bpf → vowel
  → coarse → crush → shape → distort
  → tremolo → compressor → pan → phaser → postgain
  → [delay send] + [reverb send]  (global per orbit)
```

---

## Filters

### Low-Pass Filter

| Parameter     | Aliases               | Range      | Description                                |
| ------------- | --------------------- | ---------- | ------------------------------------------ |
| `.lpf(freq~)` | `cutoff`, `ctf`, `lp` | 0–20000 Hz | Cutoff frequency; attenuates above         |
| `.lpq(q~)`    | `resonance`           | 0–50       | Resonance / Q at cutoff                    |
| `.ftype(n~)`  | —                     | 0/1/2      | Filter character: 0=12dB, 1=ladder, 2=24dB |

Shorthand: `.lpf("800:5")` = lpf=800, lpq=5

### High-Pass Filter

| Parameter     | Aliases         | Range      | Description                        |
| ------------- | --------------- | ---------- | ---------------------------------- |
| `.hpf(freq~)` | `hp`, `hcutoff` | 0–20000 Hz | Cutoff frequency; attenuates below |
| `.hpq(q~)`    | `hresonance`    | 0–50       | Resonance / Q at cutoff            |

### Band-Pass Filter

| Parameter     | Aliases       | Description      |
| ------------- | ------------- | ---------------- |
| `.bpf(freq~)` | `bandf`, `bp` | Center frequency |
| `.bpq(q~)`    | `bandq`       | Q / bandwidth    |

### Formant / Vowel Filter

| Parameter    | Description                                                            |
| ------------ | ---------------------------------------------------------------------- |
| `.vowel(v~)` | Vowel formant filter. Values: `a e i o u ae aa oe ue y uh un en an on` |

```js
// Classic filter sweep
note("c2*8").s("sawtooth")
  .lpf(sine.range(200, 4000).slow(4))
  .lpq(8)

// Vowel sequence
note("c3*4").s("sawtooth").vowel("<a e i o>")

// High-pass for kick clarity
s("bd*4").hpf(60)

// Ladder filter (Moog-style)
note("c2").s("sawtooth").lpf(800).lpq(15).ftype(1)
```

---

## Envelopes

### Amplitude Envelope (ADSR)

| Parameter        | Aliases | Description                             |
| ---------------- | ------- | --------------------------------------- |
| `.attack(t~)`    | `att`   | Time to peak amplitude (seconds)        |
| `.decay(t~)`     | `dec`   | Time to sustain level (seconds)         |
| `.sustain(l~)`   | `sus`   | Sustain level 0–1                       |
| `.release(t~)`   | `rel`   | Time from note-off to silence (seconds) |
| `.adsr(a,d,s,r)` | —       | All four at once                        |

Shorthand: `.adsr(".01:.1:.5:.2")` = attack:decay:sustain:release

```js
// Percussive — no sustain
note("c3").s("sine").attack(0.001).decay(0.3).sustain(0).release(0.1)

// Plucky synth
note("c3 e3 g3").s("sawtooth").attack(0.005).decay(0.2).sustain(0.3).release(0.4)

// Pad — slow attack
note("c3,e3,g3").s("sine").attack(1.5).sustain(0.8).release(2)
```

### Filter Envelope (LP / HP / BP)

Envelope shapes the filter cutoff over time.
Depth is in Hz (or semitones for lpenv).
Each filter has its own ADSR: prefix with `lp`, `hp`, or `bp`.

| Parameter        | Aliases | Description                                                |
| ---------------- | ------- | ---------------------------------------------------------- |
| `.lpattack(t~)`  | `lpa`   | LP filter envelope attack                                  |
| `.lpdecay(t~)`   | `lpd`   | LP filter envelope decay                                   |
| `.lpsustain(l~)` | `lps`   | LP filter envelope sustain                                 |
| `.lprelease(t~)` | `lpr`   | LP filter envelope release                                 |
| `.lpenv(depth~)` | `lpe`   | LP envelope depth (positive = opens up, negative = closes) |

Same pattern for `.hp*` and `.bp*` prefixes.

```js
// Classic acid squelch
note("c2").s("sawtooth")
  .lpf(200).lpq(15)
  .lpenv(4000).lpa(0.005).lpd(0.15).lps(0.1).lpr(0.3)

// Kick filter thump
s("bd*4").lpf(200).lpenv(2000).lpdecay(0.1)
```

### Pitch Envelope

Shapes the pitch over time — essential for punchy kicks and attack transients.

| Parameter       | Aliases | Description                                            |
| --------------- | ------- | ------------------------------------------------------ |
| `.penv(n~)`     | —       | Pitch envelope depth in semitones (signed)             |
| `.pattack(t~)`  | `patt`  | Attack time                                            |
| `.pdecay(t~)`   | `pdec`  | Decay time                                             |
| `.prelease(t~)` | `prel`  | Release time                                           |
| `.pcurve(n~)`   | —       | Curve: 0=linear, 1=exponential                         |
| `.panchor(n~)`  | —       | 0: range=[note, note+penv]; 1: range=[note−penv, note] |

```js
// 808-style kick: pitch sweeps down from +24 semitones
s("bd").bank("RolandTR808")
  .penv(24).pdecay(0.4).pcurve(1).panchor(1)

// Snare pitch bite
s("sd*4").penv(8).pdecay(0.03).pcurve(1)
```

---

## Dynamics

| Parameter              | Aliases | Description                                        |
| ---------------------- | ------- | -------------------------------------------------- |
| `.gain(n~)`            | —       | Volume (exponential, default 1). Values > 1 boost. |
| `.velocity(n~)`        | `vel`   | Velocity 0–1; multiplied with gain                 |
| `.postgain(n~)`        | —       | Gain applied after all effects                     |
| `.compressor(params~)` | —       | `"threshold:ratio:knee:attack:release"`            |

```js
// Velocity-patterned hats (accented 16th notes)
s("hh*16").gain("[0.4 1 0.6 0.8]*4")

// Sidechain-style manual gain modulation
note("c3").s("pad")
  .gain(saw.inv().range(0.1, 1).fast(4))

// Compressor on a drum bus
stack(s("bd*4"), s("hh*8")).compressor("-12:4:3:0.005:0.1")
```

---

## Delay

Delay is global per orbit — all sounds on the same orbit share one delay bus.

| Parameter            | Aliases          | Range   | Description                                 |
| -------------------- | ---------------- | ------- | ------------------------------------------- |
| `.delay(n~)`         | —                | 0–1     | Send level to delay bus                     |
| `.delaytime(t~)`     | `delayt`, `dt`   | seconds | Delay time                                  |
| `.delayfeedback(f~)` | `delayfb`, `dfb` | 0–\<1   | Feedback; **keep below 1** or infinite loop |

Shorthand: `.delay("0.5:0.25:0.4")` = level:time:feedback

```js
// 8th-note delay
note("c3 ~ e3 ~").s("piano")
  .delay(0.5).delaytime(0.25).delayfeedback(0.4)

// Synced delay (1/4 cycle = one beat in 4/4)
s("cp(1,4)").delay(0.6).delaytime(0.5).delayfeedback(0.3)

// Patterned delay time
note("g3").delay(0.4).delaytime("<0.25 0.125>").delayfeedback(0.5)
```

---

## Reverb

Reverb is global per orbit — all sounds on the same orbit share one reverb bus.
Changing `roomsize` while running is expensive; prefer setting it once.

| Parameter           | Aliases               | Range   | Description                                    |
| ------------------- | --------------------- | ------- | ---------------------------------------------- |
| `.room(n~)`         | —                     | 0–1     | Send level to reverb bus                       |
| `.roomsize(n~)`     | `rsize`, `sz`, `size` | 0–10    | Room size (0=dry, 10=huge hall)                |
| `.roomfade(t~)`     | `rfade`               | seconds | Reverb fade/RT60 time                          |
| `.roomlp(freq~)`    | `rlp`                 | Hz      | LP filter on reverb start                      |
| `.roomdim(freq~)`   | `rdim`                | Hz      | LP filter on reverb at −60dB                   |
| `.iresponse(name~)` | `ir`                  | —       | Impulse response sample for convolution reverb |

Shorthand: `.room("0.5:2")` = room:roomsize

```js
// Standard plate reverb on a pad
note("c3,e3,g3").s("piano").room(0.5).roomsize(3)

// Large hall reverb
note("c4").s("gm_violin").room(0.8).roomsize(8).roomfade(3)

// Short room
s("sd*4").room(0.2).roomsize(0.5)

// Gated reverb (short fade)
s("sd*4").room(0.6).roomsize(4).roomfade(0.08)
```

---

## Phaser

| Parameter              | Aliases         | Description                        |
| ---------------------- | --------------- | ---------------------------------- |
| `.phaser(n~)`          | `ph`            | Phaser modulation speed            |
| `.phaserdepth(n~)`     | `phd`, `phasdp` | Depth 0–1 (default 0.75)           |
| `.phasercenter(freq~)` | `phc`           | Center frequency Hz (default 1000) |
| `.phasersweep(freq~)`  | `phs`           | LFO sweep range Hz (default 2000)  |

```js
// Classic phaser effect
note("c3 e3 g3").s("sawtooth").phaser(0.5).phaserdepth(0.8)

// Fast phaser for texture
s("hh*8").phaser(4).phaserdepth(0.6)
```

---

## Distortion / Bit Effects

| Parameter      | Aliases | Range | Description                                  |
| -------------- | ------- | ----- | -------------------------------------------- |
| `.distort(n~)` | `dist`  | 0–10+ | Waveshaping distortion (0=clean)             |
| `.shape(n~)`   | —       | 0–1   | Soft waveshaping / overdrive                 |
| `.crush(n~)`   | —       | 1–16  | Bit crusher: 1=extreme lo-fi, 16=subtle      |
| `.coarse(n~)`  | —       | 1+    | Sample rate reduction factor (Chromium only) |

```js
// Distorted bass
note("c2*4").s("sawtooth").distort(3).lpf(1200)

// Lo-fi drum texture
s("bd sd hh cp").crush(8).room(0.3)

// Heavy distortion
note("c3").s("square").shape(0.8).lpf(2000)
```

---

## Tremolo (Amplitude Modulation)

| Parameter           | Aliases     | Description                                              |
| ------------------- | ----------- | -------------------------------------------------------- |
| `.tremolosync(n~)`  | `tremsync`  | Modulation speed in cycles                               |
| `.tremolodepth(n~)` | `tremdepth` | Depth 0–1                                                |
| `.tremoloskew(n~)`  | `tremskew`  | Waveform shape 0–1                                       |
| `.tremolophase(n~)` | `tremphase` | Phase offset in cycles                                   |
| `.tremoloshape(s~)` | `tremshape` | Waveform: `tri` \| `square` \| `sine` \| `saw` \| `ramp` |

```js
// Slow tremolo on pad
note("c3,e3,g3").s("sine").attack(0.5).sustain(0.8)
  .tremolosync(2).tremolodepth(0.6).tremoloshape("sine")

// Trance-gate effect (fast square tremolo)
note("c3,e3,g3").s("sawtooth")
  .tremolosync(0.125).tremolodepth(1).tremoloshape("square")
```

---

## Vibrato

| Parameter     | Aliases        | Description                |
| ------------- | -------------- | -------------------------- |
| `.vib(n~)`    | `vibrato`, `v` | Vibrato frequency in Hz    |
| `.vibmod(n~)` | `vmod`         | Vibrato depth in semitones |

```js
note("c4 d4 e4").s("sawtooth").vib(5).vibmod(0.3)

// LFO-modulated vibrato speed
note("c4").vib(sine.range(3, 8).slow(4)).vibmod(0.5)
```

---

## Panning

| Parameter          | Aliases | Description                                    |
| ------------------ | ------- | ---------------------------------------------- |
| `.pan(n~)`         | —       | Stereo position: 0=left, 0.5=center, 1=right   |
| `.jux(fn)`         | —       | Apply fn to right channel; original on left    |
| `.juxBy(amt~, fn)` | `juxby` | Jux with stereo width 0–1 (0=mono, 1=full L/R) |

```js
// Pan a hi-hat pattern across stereo field
s("hh*8").pan(sine.range(0, 1).slow(2))

// Rev only on right channel
note("c3 e3 g3 a3").jux(rev)

// Slightly widened stereo
note("c3 e3 g3").jux(x => x.add(7).gain(0.7)).juxBy(0.6)
```

---

## Sidechain / Ducking

Duck one orbit's audio when another plays — the classic sidechain compression effect.

| Parameter         | Aliases           | Description                             |
| ----------------- | ----------------- | --------------------------------------- |
| `.duckorbit(n~)`  | `duck`            | Orbit number to duck from               |
| `.duckattack(t~)` | `duckatt`, `datt` | Time to return to full volume (seconds) |
| `.duckdepth(n~)`  | —                 | Amount of ducking 0–1                   |

```js
// Classic sidechain pump: kick ducks the pad
stack(
  s("bd*4").orbit(1),
  note("c3,e3,g3").s("sawtooth").orbit(2)
    .duckorbit(1)
    .duckattack(0.15)
    .duckdepth(0.9)
    .room(0.4)
)
```

---

## Orbits

Each orbit has its own independent delay and reverb bus.
Default orbit is 1.

```js
// Different reverb settings per sound
stack(
  s("bd*4").orbit(1),                          // dry kick
  s("hh*8").orbit(2).room(0.1).roomsize(0.5),  // small room hats
  note("c3 e3").s("piano").orbit(3).room(0.6).roomsize(4)  // large reverb piano
)
```

**Warning:** pattering `.orbit()` across values creates multiple copies of the signal — use deliberately.

---

## Effect Modulation Patterns

All effect parameters accept mini-notation strings and signals:

```js
// Step-sequenced cutoff
note("c2*8").s("sawtooth").lpf("400 800 400 1600")

// Sine LFO on cutoff
note("c2*8").s("sawtooth").lpf(sine.range(200, 3000).slow(4))

// Random reverb
s("hh*8").room(rand.range(0, 0.6))

// Perlin noise on gain for organic feel
s("pad").room(0.6).gain(perlin.range(0.5, 1).slow(8))

// Pattern delay time for groove
note("c3 e3 g3").delay(0.4).delaytime("<0.25 0.125 0.25 0.5>")
```
