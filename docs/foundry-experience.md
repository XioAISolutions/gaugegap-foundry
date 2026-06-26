# Foundry Experience / Experiment

GaugeGap Foundry now has a self-contained audiovisual interface built around two distinct modes:

- **Experience** immerses the visitor in synchronized views of real finite data.
- **Experiment** exposes parameters, methods, observables, and claim boundaries.

The split is inspired by the structural distinction between `supersymmetry [experience]` and `supersymmetry [experiment]` in Ryoji Ikeda's 2014 project. The Foundry implementation is original: it does not copy the artwork's images, code, sound, installation layout, or visual sequences.

Reference: `https://www.ryojiikeda.com/project/supersymmetry/`

## Data channels

| Channel | Source | Status |
|---|---|---|
| Rössler | deterministic finite RK4 trajectory | finite numerical |
| Lorenz | deterministic finite RK4 trajectory | finite numerical |
| Thomas | deterministic finite RK4 trajectory | finite numerical |
| Z2 plaquette | exact diagonalization of the repository's 4-qubit finite Hamiltonian | exact finite |
| SU(3) geometry | exact weight multiplicities from Freudenthal recursion | exact finite representation geometry |

The browser never invents hidden scientific results. The full bundle includes `experience-data.json`, making every displayed dataset inspectable.

## Experience mode

Experience mode uses a high-contrast, full-screen canvas to present:

- rotating phase-space trajectories;
- synchronized waveform rails derived from the same trajectory;
- an exact finite Z2 gap field;
- SU(3) octet and decuplet weight geometry;
- live method, sample-count, divergence, and status readouts.

The interface is deliberately minimal and dark, but the visual composition and animation are original to GaugeGap Foundry.

## Experiment mode

Experiment mode exposes controls instead of hiding them.

For Rössler, Lorenz, and Thomas, changing a parameter recomputes a finite RK4 trajectory locally in the browser. The evidence panel shows the equations, method, sample count, and claim boundary.

For the Z2 plaquette model, the controls select the nearest point from a deterministic grid generated in Python using the repository's exact `16 x 16` Hamiltonian diagonalization. The interface reports:

- `E0`;
- `E1`;
- the finite gap `E1 - E0`;
- mean plaquette-Z expectation;
- mean link-X expectation.

It does not relabel interpolated graphics as exact results.

## Sound

Sound is **off by default**. Press the sound button or `M` to opt in.

The browser creates a local oscillator with the Web Audio API. Frequency and amplitude are driven by the selected finite signal. No audio file, microphone, analytics service, or remote endpoint is used.

## Build

```bash
foundry run foundry-experience
```

The output is written to:

```text
site/foundry-experience/
├── index.html
├── experience-data.json
└── manifest.json
```

For CI:

```bash
foundry run foundry-experience-smoke
```

To view locally:

```bash
python -m http.server 8000 --directory site/foundry-experience
```

Then open `http://localhost:8000`.

## Controls

| Key | Action |
|---|---|
| `E` | Experience mode |
| `X` | Experiment mode |
| `Space` | Pause or resume motion |
| `M` | Toggle opt-in sound |

## Reproducibility contract

The generator writes a manifest containing SHA-256 hashes and byte counts for the HTML and data files. Tests enforce that:

- two independent smoke builds are byte-identical;
- the HTML has no remote scripts or assets;
- audio remains opt-in;
- all registered scientific channels are present;
- Z2 data comes from the real exact-diagonalization path;
- SU(3) dimensions and Weyl closure are verified;
- output directories outside the repository work correctly.

## Claim boundary

This is an interface over finite computations. It does not turn a trajectory into a theorem, a finite gauge gap into a continuum mass-gap proof, or an exact weight diagram into a completed SU(3) lattice model.
