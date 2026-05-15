# Sound Sources Reference

How to select and configure what produces sound in Strudel.

---

## Core Selectors

| Function       | Description                                                           |
| -------------- | --------------------------------------------------------------------- |
| `s(name~)`     | Select sound/synth by name. Alias: `sound`                            |
| `n(index~)`    | Select sample variant index, scale degree, or chord note              |
| `note(pitch~)` | Set pitch: note name (`c3`, `eb4`), MIDI number (60), or decimal MIDI |
| `freq(hz~)`    | Set pitch by raw frequency in Hz                                      |
| `bank(name~)`  | Prepend drum machine bank name (e.g. `"RolandTR909"`)                 |

```js
s("bd sd hh cp")            // samples by name
note("c3 e3 g3 a3")        // pitch (triangle oscillator by default)
note("c3 e3").s("piano")   // pitch + sample instrument
note(60).s("sawtooth")     // MIDI number 60 = middle C
freq("220 440 880")        // A2, A3, A4
n("0 1 2").s("hh")         // sample variants via n()
```

---

## Synthesizer Waveforms

Used with `s()`.
These are the basic WebAudio oscillators — no sample files required.

| Name       | Description                                                                             |
| ---------- | --------------------------------------------------------------------------------------- |
| `sine`     | Sine wave — pure, smooth tone                                                           |
| `sawtooth` | Sawtooth wave — bright, harmonically rich; classic for leads and bass                   |
| `square`   | Square wave — hollow, woody; good for bass and retro sounds                             |
| `triangle` | Triangle wave — softer than square, similar to flute; **default when no `.s()` is set** |

```js
note("c3").s("sawtooth")   // classic synth bass/lead tone
note("c3").s("square")     // lo-fi / retro
note("c3").s("sine")       // pure sub-bass, sine pad
```

---

## Noise Generators

| Name      | Description                                                 |
| --------- | ----------------------------------------------------------- |
| `white`   | White noise — equal energy per frequency; harsh/bright      |
| `pink`    | Pink noise — equal energy per octave; more natural          |
| `brown`   | Brown noise — low-frequency bias; rumbling, warm            |
| `crackle` | Subtle crackle noise; use `.density()` to control frequency |

```js
s("white").decay(0.05).gain(0.4)    // snare transient noise
s("pink").room(0.8).gain(0.1)       // ambient texture
s("crackle").density(0.01)          // vinyl crackle effect
```

---

## FM Synthesis

FM synthesis modulates the frequency of a carrier oscillator with a modulator.
Available as parameters on any `note()` pattern.

| Parameter        | Aliases | Description                                      |
| ---------------- | ------- | ------------------------------------------------ |
| `.fm(n~)`        | —       | FM index (modulation depth); 0 = no modulation   |
| `.fmh(ratio~)`   | —       | Harmonicity ratio: 1=unison, 2=octave, 1.5=fifth |
| `.fmattack(t~)`  | `fmatt` | FM envelope attack time                          |
| `.fmdecay(t~)`   | `fmdec` | FM envelope decay time                           |
| `.fmsustain(l~)` | `fmsus` | FM envelope sustain level                        |
| `.fmenv(type~)`  | `fme`   | Envelope type: `lin` or `exp`                    |

Up to 8 independent FM operators: `fm2`, `fmh2`, `fmatt3`, etc.

```js
// Metallic bell-like sound
note("c4 e4 g4").fm(3).fmh(2.1).fmattack(0.01).fmdecay(0.4).fmsustain(0)

// Wobbly bass
note("c2").s("triangle").fm(sine.range(0, 8).slow(2))

// Classic FM electric piano approximation
note("c3 e3 g3").fm(1.5).fmh(2).fmattack(0.005).fmdecay(1).fmsustain(0.3)
```

---

## Additive Synthesis

Build timbres from harmonic partials using the `user` synth type.

| Parameter                | Description                                        |
| ------------------------ | -------------------------------------------------- |
| `.partials([m1,m2,...])` | Magnitude of each harmonic (index 1 = fundamental) |
| `.phases([p1,p2,...])`   | Phase offset of each harmonic                      |

```js
note("c3").s("user").partials([1, 0.5, 0.25, 0.1])   // sawtooth-like approximation
note("c3").s("user").partials([1, 0, 1, 0, 0.5])      // odd harmonics (square-like)
```

---

## Wavetable Synthesis

Prefix any AKWF wavetable name with `wt_` — the sample auto-loops as a single-cycle waveform.

```js
note("c3").s("wt_digital")
note("c3").s("wt_digi")
note("c3").s("wt_oboe")
note("<c3 e3 g3>").s("<wt_digital wt_sine wt_triangle>")
```

Wavetable names follow the AKWF library conventions.

---

## Drum Samples (Default)

Strudel ships with a default sample library.
Drum sounds are accessed by short name.

| Name   | Sound                    |
| ------ | ------------------------ |
| `bd`   | Bass drum / kick         |
| `sd`   | Snare drum               |
| `rim`  | Rimshot                  |
| `cp`   | Clap                     |
| `hh`   | Closed hi-hat            |
| `oh`   | Open hi-hat              |
| `cr`   | Crash cymbal             |
| `rd`   | Ride cymbal              |
| `ht`   | High tom                 |
| `mt`   | Mid tom                  |
| `lt`   | Low tom                  |
| `sh`   | Shaker / maracas         |
| `cb`   | Cowbell                  |
| `tb`   | Tambourine               |
| `perc` | Miscellaneous percussion |
| `misc` | Miscellaneous            |
| `fx`   | Sound effects            |

---

## Drum Machine Banks

`.bank(name)` prepends the bank name with an underscore to the sample name:
`s("bd").bank("RolandTR909")` → plays `_RolandTR909_bd`.

| Bank name        | Machine             |
| ---------------- | ------------------- |
| `RolandTR808`    | Roland TR-808       |
| `RolandTR909`    | Roland TR-909       |
| `RolandTR707`    | Roland TR-707       |
| `AkaiLinn`       | Akai/Linn LM-1      |
| `RhythmAce`      | Ace Tone Rhythm Ace |
| `ViscoSpaceDrum` | Visco Space Drum    |

```js
// Consistent bank for all sounds in a stack
stack(
  s("bd*4"),
  s("~ cp ~ cp"),
  s("hh*8").gain(0.5)
).bank("RolandTR909")

// Pattern the bank itself
s("bd sd hh").bank("<RolandTR909 RolandTR808>")

// Per-sound bank control
s("bd").bank("RolandTR808").n(0)   // select specific 808 variation
```

---

## General MIDI (GM) Instruments

All 128 General MIDI instruments are available with the `gm_` prefix.
Names use underscores for spaces, all lowercase.

```js
note("c3 e3 g3").s("gm_acoustic_grand_piano")
note("c2 g2").s("gm_acoustic_bass")
note("c3 e3").s("gm_epiano1")
note("c4").s("gm_voice_oohs")
note("c3").s("gm_tuba")
note("c3").s("gm_electric_guitar_muted")
note("c3").s("gm_slap_bass_1")
note("c4 d4 e4").s("gm_blown_bottle")
```

Common picks:

- `gm_acoustic_grand_piano` — acoustic piano
- `gm_epiano1` — electric piano (Rhodes-like)
- `gm_acoustic_bass` — upright bass
- `gm_slap_bass_1` — slap bass
- `gm_string_ensemble_1` — strings
- `gm_pad_new_age` — pad
- `gm_choir_aahs` — choir

---

## Loading Custom Samples

### From GitHub

Expects a `strudel.json` manifest at the repo root:

```js
samples('github:username/repo')
samples('github:username/repo/branch')
```

### From URL

```js
samples({
  kick: 'https://example.com/sounds/kick.wav',
  snare: ['https://example.com/sd1.wav', 'https://example.com/sd2.wav'],
  '_base': 'https://example.com/sounds/'
})
```

### From a JSON manifest

```js
samples('https://example.com/strudel.json')
```

### Pitched samples (multi-sample)

```js
samples({
  piano: {
    'A4': 'piano-a4.wav',
    'C5': 'piano-c5.wav',
    'E5': 'piano-e5.wav'
  }
})
```

### Alias existing sounds

```js
soundAlias('kick', 'bd')    // "kick" now plays "bd"
```

---

## Sampler Playback Controls

These modify how a sample file is read.

| Parameter        | Aliases  | Range   | Description                                                        |
| ---------------- | -------- | ------- | ------------------------------------------------------------------ |
| `.begin(n~)`     | —        | 0–1     | Start playback at this position in sample                          |
| `.end(n~)`       | —        | 0–1     | End playback at this position in sample                            |
| `.speed(n~)`     | —        | any     | Playback speed; 2=+1 octave, −1=reversed                           |
| `.loop(n~)`      | —        | 0/1     | Loop sample (1=on)                                                 |
| `.loopBegin(n~)` | `loopb`  | 0–1     | Loop region start                                                  |
| `.loopEnd(n~)`   | `loope`  | 0–1     | Loop region end                                                    |
| `.cut(group~)`   | —        | integer | Cut group: stops other events in same group (for hats: oh cuts hh) |
| `.clip(f~)`      | `legato` | 0–1+    | Multiply event duration; truncates at end                          |
| `.loopAt(n~)`    | —        | cycles  | Fit sample to n cycles by adjusting speed                          |
| `.fit()`         | —        | —       | Fit sample to its event duration                                   |

```js
// Sample slicing region
s("breaks165").begin(0.25).end(0.75)

// Reverse playback
s("piano:2").speed(-1)

// Cut group: open hat stops closed hat
s("hh*4, oh(1,4,3)").cut(1)

// Loop sample + loop region
s("pad").loop(1).loopBegin(0.1).loopEnd(0.9)

// Fit break to 2 cycles
s("breaks165").loopAt(2)
```

---

## Granular / Slicing

| Parameter          | Description                                               |
| ------------------ | --------------------------------------------------------- |
| `.chop(n~)`        | Cut sample into n equal pieces; triggers each in sequence |
| `.striate(n~)`     | Progressively slice and trigger n pieces                  |
| `.slice(n, pat~)`  | Chop into n slices; trigger by index via pattern          |
| `.splice(n, pat~)` | Like `slice` but stretches each slice to step duration    |

```js
// Granular texture from a break
s("breaks165").chop(16).rev().room(0.5)

// Manual slice sequencing
s("breaks165").slice(8, "0 1 2 3 4 5 6 7")

// Splice with time-stretching
s("breaks165").splice(8, "0 2 4 6 1 3 5 7")
```

---

## MIDI Output

```js
note("c3 e3 g3").midi()               // send to default MIDI output
note("c3").midi("IAC Driver")          // specific device by name
note("c3").midichan(2)                 // MIDI channel 1–16
note("c3").ccn(74).ccv(sine.range(0,1).slow(4))  // CC modulation
note("c3").midibend(sine2.slow(2))     // pitch bend −1 to 1
note("c3").miditouch(0.8)             // aftertouch 0–1
note("c3").progNum(5)                  // program change

// MIDI transport
s("bd*4").midicmd("clock")            // send MIDI clock
```

| Parameter          | Description                                     |
| ------------------ | ----------------------------------------------- |
| `.midi(device?)`   | Route to MIDI output                            |
| `.midichan(n~)`    | Channel 1–16                                    |
| `.midiport(name~)` | Output device name                              |
| `.ccn(n~)`         | CC number                                       |
| `.ccv(v~)`         | CC value 0–1                                    |
| `.midibend(n~)`    | Pitch bend −1 to 1                              |
| `.miditouch(n~)`   | Key aftertouch 0–1                              |
| `.progNum(n~)`     | Program change 0–127                            |
| `.sysex(data)`     | SysEx byte array                                |
| `.midicmd(cmd~)`   | Transport: `clock`, `start`, `stop`, `continue` |

---

## OSC / SuperDirt

Requires the node.js OSC bridge (`pnpm run osc` in the Strudel repo):

```js
note("c3 e3 g3").osc()    // send events as OSC messages to SuperDirt
```

---

## Visual Feedback (REPL)

See [`visual-feedback.md`](visual-feedback.md) for the full visualizer reference, including when to suggest each one.
Available: `pianoroll()`, `_pianoroll()`, `punchcard()`, `scope()`, `spectrum()`, `spiral()`, `pitchwheel()`, `.color(pat~)`.
