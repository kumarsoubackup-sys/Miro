## AI / Robotics / Lasers Scan v1

This batch tests the first broad pick pipeline on AI-, robotics-, and laser-adjacent names. The goal is not to prove the picks are correct; it is to see whether the engine surfaces names that look directionally similar to an AleaBito-style bottleneck lens and whether it can force an expression choice.

### Top picks

1. `MP` -> `shares`
   - Highest combined score in the batch.
   - The engine likes the rare-earth sovereignty + robotics + defense overlap and still sees a real recognition gap.
   - It does not think the options case is strong enough to outrank stock.

2. `HUBB` -> `shares`
   - Strong bottleneck fit through AI power delivery and transformer scarcity.
   - Lower asymmetry than the photonics names, but high durability and clean stock expression.

3. `MU` -> `shares`
   - Still scores well on HBM and packaging duration.
   - The engine reads this as a stock thesis rather than a long-vol thesis.

4. `VRT` -> `shares`
   - Cooling deployment bottleneck remains attractive.
   - Good systems-constraint story, but options expression does not clear the bar.

5. `ONTO` -> `shares`
   - Metrology/process-control exposure to AI packaging is attractive and underfollowed relative to foundries and memory.

### Notable laser / photonics names

- `SIVE` ranked `6`
  - Strong mispricing score.
  - The engine broadly agrees with the equity-thesis direction.
  - It still prefers `shares` because the current framework penalizes execution risk, listing quality, and options implementation.

- `COHR` ranked `7`
  - Positive but not elite.
  - The vertical-integration story is real, but the business mix reduces the perception of a clean bottleneck expression.

- `LITE` ranked `9` -> `reject`
  - This is an intentional outcome of the current model.
  - The engine treats `LITE` as real but already well recognized, so it is not seeing enough mispricing left.

- `POET` ranked `10` -> `reject`
  - The engine is penalizing thin listing quality and execution risk heavily.

### What this says about the current engine

- It is doing a decent job of finding plausible bottleneck-aligned equities.
- It is not yet behaving like a highly aggressive small-cap discovery engine.
- It is strongly biased toward:
  - clearer public-market vehicles
  - simpler equity expressions
  - lower implementation friction
- That means it is probably under-selecting some of the obscure photonics names that a more AleaBito-like approach would push higher.

### Main takeaway

The current engine is better at finding `high-quality structural equity ideas` than `hidden explosive picks`. That is useful, but it is not yet enough. The next iteration should focus on improving how the model rewards:

- underfollowed small-cap bottlenecks
- valuation nonlinearity
- network-position asymmetry
- ecosystem leverage despite near-term financial messiness

That is the gap between this batch and the kind of outputs the user is actually trying to reproduce.
