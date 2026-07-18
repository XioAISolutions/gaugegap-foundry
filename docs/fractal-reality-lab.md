# Fractal Reality Lab

Fractal Reality Lab is the first public experience that makes the relationship between GaugeGap Foundry and BrainSNN concrete:

- **GaugeGap Foundry** runs a finite, reproducible experiment and measures the gap between a user's prediction and a feature comparison.
- **BrainSNN** receives documented orbit features and turns them into an inspectable deterministic spike visualization.
- **The browser experience** joins the Mandelbrot set, the corresponding Julia set, the finite orbit, sonification, analogue comparisons, a 3D Mandelbulb, and a shareable result card.

The lab asks a compelling question without silently converting it into a claim:

> Is the Mandelbrot set the code of reality?

The experiment can demonstrate finite mathematics and quantify descriptive similarities. It cannot establish that one recurrence literally generates every visually related physical system.

## Run it

Generate the deterministic evidence bundle:

```bash
foundry run fractal-reality-lab
```

Run the reduced smoke build:

```bash
foundry run fractal-reality-smoke
```

Open the self-contained browser interface:

```text
site/fractal-reality-lab/index.html
```

The interface has no CDN or JavaScript framework dependency. WebAudio is used only after a user gesture. WebGL is used for the live Mandelbulb and fails gracefully when unavailable.

## Repeated experiment loop

```text
Observe → perturb → simulate → measure the gap → learn → fork
```

At each selected complex point `c`, the lab:

1. iterates `z[n+1] = z[n]^2 + c` from `z[0] = 0`;
2. records whether and when the finite orbit escapes;
3. renders the corresponding Julia escape-time field;
4. extracts bounded features such as periodicity, entropy, instability, angular turning, and a finite Lyapunov-style proxy;
5. maps the orbit to documented sound events;
6. encodes the features into seven deterministic leaky-integrate-and-fire regions;
7. compares the feature vector with an explicitly labelled analogue profile;
8. reports the difference between the user's predicted similarity and the measured feature similarity as the **Gauge Gap**;
9. exports a shareable card that preserves the evidence label and claim boundary.

## Evidence classes

### Demonstrated connection

A finite equation-level or deliberately constructed connection is present. Examples include Mandelbrot/Julia dynamics, finite escape-time fields, a cardioid polar response, optical caustics, wave interference, the chosen sonification mapping, and the Mandelbulb construction.

This label does **not** mean two systems share one physical cause merely because part of their mathematics or geometry is related.

### Structural analogy

A feature comparison identifies measurable resemblance, but no shared generator has been demonstrated. Neuron branching, lightning, rivers, trees, and rose windows are treated this way.

### Philosophical interpretation

The statement is meaningful as metaphor or worldview but is not an output of the finite experiment. “All things are one thing,” “the Mandelbrot set is the code of reality,” and “the Eiffel Tower is a 3D Mandelbrot tower” stay in this class unless stronger evidence is supplied.

## BrainSNN bridge

The seven visualization regions are:

- thalamic input;
- orbit memory;
- periodicity;
- boundary salience;
- symmetry;
- novelty;
- integration.

Their drives are explicit functions of the orbit feature vector. The recurrent weights are fixed and exported. The spike trains are deterministic for a given finite report.

This is a transparent presentation bridge, not a trained biological model, a consciousness model, or a claim that named regions correspond to real cortical anatomy.

## Sonification mapping

The sound engine maps:

- orbit order → event time;
- orbit angle and magnitude → pitch/harmonic selection;
- real component → stereo position;
- magnitude → gain;
- measured periodicity → note duration.

A more complex sound near a boundary is an effect of this declared mapping and the finite orbit. It is not evidence of an objective hidden cosmic scale.

## 3D boundary

The interface ray-marches a power-controlled Mandelbulb. The Mandelbulb is a recognized family of 3D fractal constructions inspired by Mandelbrot-style iteration. It is not the uniquely defined canonical three-dimensional Mandelbrot set.

Organic resemblance is presented as an observation. A claim that broccoli, lungs, architecture, and the Mandelbulb share one generator would require independent mechanistic evidence.

## Main artifacts

- `src/gaugegap/fractal_reality.py` — finite orbit analysis, Julia grids, features, sonification events, BrainSNN encoding, analogue library, comparisons, and hashed manifest.
- `scripts/run_fractal_reality_lab.py` — reproducible artifact generator.
- `site/fractal-reality-lab/` — interactive browser experience.
- `tests/test_fractal_reality.py` — deterministic and boundary tests.
- `config/foundry.d/fractal_reality.yaml` — Foundry orchestration units.

## Claim boundary

Allowed language:

- the Mandelbrot recurrence produces finite orbits with complex and often self-similar structure;
- Mandelbrot and Julia sets are mathematically related;
- declared mathematical properties can be sonified;
- recurring branching, symmetry, and scale patterns can be compared quantitatively;
- the lab distinguishes equation-level connection, structural analogy, and philosophical interpretation;
- BrainSNN provides an inspectable feature-to-spike presentation layer.

Do not claim:

- the lab proves the Mandelbrot set is the literal code of physical reality;
- all visually similar forms obey `z² + c`;
- the sonification discovers an objective cosmic harmony;
- the Eiffel Tower is derived from a Mandelbulb;
- the spike visualization is a biological, conscious, or generally intelligent brain;
- a finite feature score proves a common physical mechanism.
