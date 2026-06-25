# Attractor Forge — certified boundaries around strange-attractor numerics

Attractor Forge extends FlowGap from finite PDE surrogates into finite nonlinear
ODE dynamics.  Its first registered systems are Rössler, Lorenz, and Thomas.
The goal is not to render a familiar butterfly or spiral; it is to turn each
visual into a reproducible evidence bundle whose exact, numerical, and formal
claims are kept separate.

## Systems

### Rössler

\[
\dot x=-y-z,\qquad
\dot y=x+ay,\qquad
\dot z=b+z(x-c).
\]

Default parameters are `a=0.2`, `b=0.2`, `c=5.7`.  The exact divergence is

\[
\nabla\cdot f=a+x-c.
\]

It is **not globally negative**.  The formal certificate therefore proves only
the honest conditional statement

\[
x\le c-a-\delta,\;\delta\ge0
\quad\Longrightarrow\quad
\nabla\cdot f\le-\delta.
\]

### Lorenz

\[
\dot x=\sigma(y-x),\quad
\dot y=x(\rho-z)-y,\quad
\dot z=xy-\beta z.
\]

The exact divergence is constant:

\[
\nabla\cdot f=-(\sigma+1+\beta).
\]

For non-negative `sigma` and `beta`, Lean and Coq discharge the global bound
`div f <= -1`.

### Thomas

\[
\dot x=\sin y-bx,\quad
\dot y=\sin z-by,\quad
\dot z=\sin x-bz.
\]

The exact divergence is `-3b`; for `b>0`, the certificate proves it is strictly
negative.  Only the exact origin is registered as a fixed point.  The code does
not claim to isolate every additional root.

## Evidence ladder

Each run emits the following layers.

1. **Equation layer** — named vector field, analytic Jacobian, divergence, and
   known fixed points.
2. **Deterministic integration** — fixed-step classical RK4 with explicit `dt`,
   step count, transient, initial state, and parameters.
3. **Local stability** — fixed-point residuals and Jacobian eigenvalues.
4. **Return dynamics** — linearly interpolated Poincaré crossings and a return
   map.
5. **Variational dynamics** — the complete finite-time Lyapunov spectrum from a
   Benettin/QR tangent integration.
6. **Cross-check** — short-horizon `dt`, `dt/2`, `dt/4` endpoint comparison and
   observed RK4 order.  This is deliberately short-horizon because long chaotic
   trajectories should diverge even when both integrations are correct.
7. **Secondary diagnostics** — sensitivity threshold time, dominant FFT peaks,
   sampled recurrence rate, a log-log correlation-dimension fit, and optional
   parameter/maxima sweep.
8. **Formal boundary** — hole-free Lean/Coq proof of only the exact algebraic
   divergence inequality appropriate to that system.
9. **Reproducible artifacts** — JSON summary, JSONL ledger, CSV trajectories,
   SVG projections, formal sources, report, object hash, and a dependency-free
   rotating HTML explorer.

## What the numbers do and do not establish

A positive finite-time Lyapunov estimate is strong numerical evidence of local
sensitivity for the configured integration.  It is not by itself a theorem that
the continuous system possesses a strange attractor.  The Kaplan–Yorke number is
computed from those finite-time exponents and inherits that limitation.

The correlation-dimension result is a finite sampled fit over automatically
selected distance quantiles.  Its reported `R²` is fit evidence, not a proof of a
fractal invariant.  Bifurcation-style plots are finite local-maxima samples, not
complete bifurcation diagrams.  FFT peaks describe the sampled observable, not a
coordinate-independent spectrum.

The divergence certificates establish local or global phase-volume contraction.
Contraction alone does not prove chaos.  This separation is intentional.

## Run it

```bash
python scripts/run_attractor_forge.py \
  --system rossler \
  --params a=0.2,b=0.2,c=5.7 \
  --dt 0.01 \
  --steps 30000 \
  --transient 5000 \
  --lyapunov-steps 30000 \
  --bifurcation-points 24 \
  --output-dir results/flowgap-0002-attractor-forge
```

Other built-ins:

```bash
python scripts/run_attractor_forge.py --system lorenz --bifurcation-points 24
python scripts/run_attractor_forge.py --system thomas --steps 50000
```

The generated `attractor_explorer.html` is self-contained and uses no external
JavaScript library.  Its rotation is a viewer control, not additional data.

## Adding another nonlinear system

Register an `AttractorSystem` in `src/gaugegap/flowgap_attractors.py` with:

- a unique name and explicit parameter schema;
- default parameters and initial state;
- a three-component right-hand side;
- an analytic 3×3 Jacobian;
- exact divergence;
- only fixed points that the implementation can state honestly;
- a matching divergence certificate, or an explicit reason no certificate is
  currently emitted.

Then add tests that compare the analytic Jacobian to central finite differences,
check every registered fixed-point residual, verify deterministic integration,
and assert the formal source has no `sorry` or `Admitted`.

## Claim boundary

Attractor Forge is a finite-time numerical laboratory for nonlinear ODEs.  It
makes no formal claim of chaos, global attraction, ergodicity, mixing, or a
rigorous fractal dimension.  Its machine-checked claims are limited to the exact
algebraic divergence bounds printed in each bundle.  It is a FlowGap benchmark,
not a Millennium-problem result and not a continuum-fluid regularity argument.
