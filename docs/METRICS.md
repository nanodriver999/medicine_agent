# Objective coverage and cost curves

For the **synthetic offline fixture only**:
- QED is maximized, synthetic `fixture_risk` is minimized.
- Hypervolume is computed in a fixed normalized square, reference point
  `(qed=0, fixture_risk=1)`. Missing/unmeasured scores are excluded.
- A higher hypervolume is desirable only **under the same declared objectives**.
- Cost curves record the highest observed synthetic composite objective and
  hypervolume at successive evaluation costs.
- The synthetic risk oracle is not biologically meaningful, so higher fixture
  hypervolume is **not** evidence of better drug candidates.

For real ADMET endpoint comparisons, independently verify task direction, units,
score scale and a preregistered normalization/reference point before calculating
hypervolume. Do not reuse the [0,1] fixture reference point for arbitrary real
model outputs.
