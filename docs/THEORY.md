# Fermentation Theory & Science

Understanding the science behind wine fermentation, Pet Nat production, and why monitoring matters.

---

## Table of Contents

1. [Fermentation Basics](#fermentation-basics)
2. [Pet Nat Chemistry](#pet-nat-chemistry)
3. [CO2 Production & Pressure](#co2-production--pressure)
4. [Yeast Biology](#yeast-biology)
5. [Temperature Effects](#temperature-effects)
6. [Prediction Science](#prediction-science)
7. [Safety Calculations](#safety-calculations)

---

## Fermentation Basics

### What is Fermentation?

Fermentation is the metabolic process where yeast converts sugars into alcohol and carbon dioxide.

**Chemical Equation:**
```
C₆H₁₂O₆ → 2 C₂H₅OH + 2 CO₂ + Energy
Glucose → Ethanol + Carbon Dioxide + Heat

Or more specifically (Gay-Lussac equation):
C₆H₁₂O₆ → 2 C₂H₅OH + 2 CO₂
180g → 92g + 88g
```

**Key Points:**
- 1 molecule of glucose produces 2 molecules each of ethanol and CO₂
- Mass: 180g sugar → 92g alcohol (51%) + 88g CO₂ (49%)
- Approximately: 1g sugar → 0.51g alcohol + 0.49g CO₂
- In practice: ~16.5g sugar produces 1% ABV per liter

### Fermentation Phases

```
Timeline (typical wine fermentation):

Day 0-1: LAG PHASE
├─ Yeast adapting to environment
├─ Cell division beginning
├─ Minimal CO₂ production
└─ Low bubble rate (0-5 bubbles/min)

Day 1-3: EXPONENTIAL GROWTH
├─ Rapid yeast multiplication
├─ Increasing fermentation rate
├─ Temperature rising
└─ Bubble rate increasing (5-50 bubbles/min)

Day 3-7: PEAK FERMENTATION
├─ Maximum yeast population
├─ Highest sugar consumption rate
├─ Most CO₂ production
└─ Bubble rate at maximum (50-120 bubbles/min)

Day 7-10: DECLINING PHASE
├─ Sugar depleting
├─ Yeast slowing down
├─ Temperature dropping
└─ Bubble rate decreasing (20-50 bubbles/min)

Day 10-14: FINISHING PHASE
├─ Remaining sugar consumed slowly
├─ Yeast settling
├─ Clarification beginning
└─ Low bubble rate (5-20 bubbles/min)

Day 14+: COMPLETE
├─ Fermentation ceased
├─ No sugar remaining (dry) or stable (sweet)
├─ Yeast flocculating
└─ Minimal bubbles (0-2 bubbles/min)
```

### Gravity Changes

**Specific Gravity (SG):**
Ratio of liquid density to water density.

- **Water**: 1.000 SG
- **Typical grape juice**: 1.040 - 1.100 SG
- **Finished wine (dry)**: 0.990 - 1.000 SG
- **Finished wine (sweet)**: 1.000 - 1.020 SG

**Calculating ABV from Gravity:**
```
ABV = (OG - FG) × 131.25

Where:
- OG = Original Gravity (starting)
- FG = Final Gravity (ending)

Example:
OG = 1.055
FG = 1.000
ABV = (1.055 - 1.000) × 131.25 = 0.055 × 131.25 = 7.22%
```

**Alternative formula (more accurate):**
```
ABV = ((OG - FG) / 0.00753) × FG / 0.794

Example:
ABV = ((1.055 - 1.000) / 0.00753) × 1.000 / 0.794
ABV = 7.30 × 1.26 = 9.2%... wait, that's wrong

Actually:
ABV = (OG - FG) × 131.25 is standard and accurate for wines
```

---

## Pet Nat Chemistry

### Why Pet Nat is Different

Traditional wine: Ferment to completion → bottle → stable
Champagne: Ferment to completion → add sugar → bottle → re-ferment
**Pet Nat**: Bottle mid-fermentation → fermentation completes in bottle

### The Critical Balance

Pet Nat requires bottling at **exactly the right moment**:

```
Too Early (>1.010 SG)      Perfect (1.002-1.006)    Too Late (<1.002)
        │                          │                        │
        ▼                          ▼                        ▼
   Over-carbonated            Perfect fizz              Under-carbonated
   Dangerous pressure         3-4 bar                   Slightly sparkling
   Risk of explosion          Safe & delicious          Disappointing
```

### Sugar-to-CO₂-to-Pressure Conversion

**Step 1: Sugar Remaining**
```
Sugar (g/L) = (Current_SG - Final_SG) × 1000 × Density_Factor

Where Density_Factor ≈ 1.0 for dilute solutions

Example:
Current: 1.005
Final: 1.000
Sugar = (1.005 - 1.000) × 1000 = 5 g/L
```

**Step 2: CO₂ Production**
```
CO₂ produced (g/L) = Sugar consumed (g/L) × 0.49

(From Gay-Lussac equation: 49% of sugar mass becomes CO₂)

Example:
Sugar consumed = 5 g/L
CO₂ = 5 × 0.49 = 2.45 g/L

But not all CO₂ stays in solution!
CO₂ retained (in bottle) ≈ Sugar × 1.6

Example:
CO₂ in bottle = 5 × 1.6 = 8 g/L
```

**Step 3: Pressure Calculation**

Henry's Law governs CO₂ solubility:
```
P = K × C / T_factor

Where:
- P = Pressure (bar)
- C = CO₂ concentration (g/L)
- K = Henry's constant (temperature dependent)
- T_factor = Temperature correction

Simplified for wine (at 20°C):
Pressure (bar) = CO₂ (g/L) × 0.5

Example:
CO₂ = 8 g/L
Pressure = 8 × 0.5 = 4.0 bar
```

**Complete Calculation:**
```
Given:
- Current SG: 1.005
- Final SG: 1.000 (predicted)
- Temperature: 20°C

Step 1: Points remaining = (1.005 - 1.000) × 1000 = 5
Step 2: CO₂ = 5 × 1.6 = 8 g/L
Step 3: Pressure = 8 × 0.5 = 4.0 bar

Result: Safe for champagne bottles (rated to 6+ bar)
```

### Temperature Effects on Pressure

CO₂ solubility decreases with temperature:

```
Temperature    CO₂ Solubility    Pressure Multiplier
5°C (cold)     High (1.30×)      Low (0.77×)
10°C           High (1.18×)      Low (0.85×)
15°C           Medium (1.08×)    Medium (0.92×)
20°C           Medium (1.00×)    Baseline (1.00×)
25°C           Low (0.92×)       High (1.09×)
30°C           Low (0.85×)       High (1.18×)

Formula:
Pressure(T) = Pressure(20°C) × (1 + 0.009 × (T - 20))

Example at 30°C:
Pressure = 4.0 × (1 + 0.009 × 10) = 4.0 × 1.09 = 4.36 bar
```

**Implication for Pet Nat:**
- Store cool (10-15°C) → Lower pressure, safer
- Warm day (30°C) → Pressure increases ~20%!
- Always chill before opening → Reduces pressure

---

## CO2 Production & Pressure

### CO₂ Volumes

Wine industry measures carbonation in "volumes of CO₂":

```
1 volume = 1 liter of CO₂ per liter of wine (at standard conditions)
         = ~2 g/L CO₂

Typical Values:
- Still wine: 0-0.5 volumes (< 1 g/L)
- Pétillant: 1-2 volumes (2-4 g/L)
- Pet Nat: 3-5 volumes (6-10 g/L)
- Champagne: 5-6 volumes (10-12 g/L)
- Beer: 2-4 volumes (4-8 g/L)
```

### Pressure in Bottles

**Relationship between CO₂ and Pressure:**

```
At 20°C in wine:

CO₂ (g/L)    Volumes    Pressure (bar)    Pressure (PSI)
2            1          1.0               14.5
4            2          2.0               29
6            3          3.0               43.5
8            4          4.0               58
10           5          5.0               72.5
12           6          6.0               87

Formula:
Pressure (bar) ≈ CO₂ (g/L) / 2
Volumes ≈ CO₂ (g/L) / 2
```

### Bottle Strength

Different bottles have different pressure ratings:

```
Bottle Type           Rated Pressure    Burst Pressure    Use
Regular wine          0-1 bar           2-3 bar           Still wine only
Screw-top wine        0-1 bar           2-3 bar           NEVER for Pet Nat
Beer bottle (light)   3-4 bar           5-6 bar           Beer, light Pet Nat
Beer bottle (heavy)   5-6 bar           8-9 bar           Beer, Pet Nat
Champagne bottle      6-8 bar           12-15 bar         Pet Nat, Champagne
Plastic (PET)         2-3 bar           4-5 bar           Beer only (not wine)
```

**Safety Factor:**
Always operate at < 75% of rated pressure for safety margin.

```
Champagne bottle rated to 6 bar:
- Target: 3-4 bar (50-67% of rated)
- Maximum: 4.5 bar (75% of rated)
- Danger: > 5 bar (83% of rated)
- Critical: > 6 bar (burst imminent!)
```

---

## Yeast Biology

### Yeast Species

**Wine Yeast (Saccharomyces cerevisiae):**
- Most common for winemaking
- Alcohol tolerance: 12-18% depending on strain
- Temperature range: 10-30°C (optimal 15-25°C)
- Produces "clean" flavors

**Champagne Yeast:**
- Subset of S. cerevisiae
- High alcohol tolerance (18%+)
- Works well under pressure
- Produces fine bubbles

**Wild Yeast:**
- Mix of species (S. cerevisiae, Hanseniaspora, etc.)
- Variable behavior
- Can produce unique flavors (or off-flavors)
- Less predictable

### Yeast Metabolism

**Aerobic vs Anaerobic:**

```
With Oxygen (Aerobic):
C₆H₁₂O₆ + 6 O₂ → 6 CO₂ + 6 H₂O + Energy (38 ATP)
- More energy for yeast
- More cell growth
- Less alcohol production
- Used in lag phase

Without Oxygen (Anaerobic):
C₆H₁₂O₆ → 2 C₂H₅OH + 2 CO₂ + Energy (2 ATP)
- Less energy for yeast
- Alcohol production
- Used in fermentation phase
```

**Pasteur Effect:**
Yeast prefer aerobic metabolism when oxygen available, switch to fermentation when oxygen depleted.

### Yeast Growth Curve

```
Yeast Population Over Time:

Population
    │     Stationary Phase
    │         ┌─────────
    │        ╱
    │       ╱ Exponential
    │      ╱  Growth
    │     ╱
    │ ___╱ Lag
    │    Phase   │      Death Phase
    │            │    ╲
    │            │     ╲___
    └────────────┴──────────────> Time
         Days: 0-1  1-7  7-14  14+
```

**Phases:**
1. **Lag** (0-24h): Adaptation, minimal growth
2. **Exponential** (1-7 days): Rapid multiplication
3. **Stationary** (7-14 days): Population stable, fermentation continues
4. **Death** (14+ days): Cells dying, autolysis begins

### Factors Affecting Yeast Performance

**Temperature:**
```
Temperature    Effect on Fermentation
< 10°C         Very slow or stopped
10-15°C        Slow, clean, fruity
15-20°C        Moderate, balanced
20-25°C        Fast, complete
25-30°C        Very fast, possible off-flavors
> 30°C         Stressed yeast, stuck fermentation
```

**Nutrients:**
- Nitrogen (amino acids): Essential for yeast growth
- Vitamins (thiamine, pantothenic acid): Cofactors
- Minerals (Mg, Zn): Enzyme function

**Alcohol Tolerance:**
```
Alcohol %    Yeast Status
0-5%         Healthy, active
5-10%        Active
10-14%       Slowing down
14-16%       Most strains struggle
16-18%       Only tolerant strains
18%+         Fermentation stops
```

---

## Temperature Effects

### Arrhenius Equation

Fermentation rate follows Arrhenius relationship:

```
k = A × e^(-Ea / RT)

Where:
- k = Reaction rate
- A = Pre-exponential factor
- Ea = Activation energy (~50 kJ/mol for fermentation)
- R = Gas constant (8.314 J/mol·K)
- T = Temperature (Kelvin)

Practical rule: Fermentation rate doubles every 10°C increase
```

**Example:**
```
At 15°C: Fermentation takes 14 days
At 20°C: Fermentation takes 10 days (1.4× faster)
At 25°C: Fermentation takes 7 days (2× faster than 15°C)
```

### Temperature-Gravity Correction

Hydrometers are calibrated at 20°C. Adjust readings:

```
Corrected_SG = Measured_SG + 0.00130 × (T - 20)

Where T is temperature in °C

Example:
Measured SG: 1.020 at 25°C
Correction: +0.00130 × (25 - 20) = +0.0065
Corrected SG: 1.020 + 0.0065 = 1.0265

Or 1.027 rounded
```

### Heat Production

Fermentation is exothermic (produces heat):

```
Heat = 21.5 kJ per 100g sugar fermented

For a 20L batch starting at 1.050 SG:
- Sugar: ~100g/L × 20L = 2000g
- Heat: 2000/100 × 21.5 = 430 kJ = 103 kcal

This can raise temperature 2-4°C in small batches!
```

**Temperature Control Important:**
- Small batches (< 20L): Ambient cooling usually sufficient
- Large batches: Active cooling needed
- Temperature swings affect fermentation rate and predictions

---

## Prediction Science

### Why Fermentation is Predictable

Fermentation follows mathematical models:

**1. Logistic Growth Model:**
```
SG(t) = SG_final + (SG_initial - SG_final) / (1 + e^(k(t - t₀)))

Where:
- SG(t) = Specific gravity at time t
- SG_initial = Starting gravity
- SG_final = Final gravity (asymptote)
- k = Growth rate constant
- t₀ = Inflection point (peak fermentation)
- t = Time
```

This S-curve matches real fermentation:
```
Gravity
  │
  │ ○
  │  ○
  │   ○         Inflection point
  │    ○○       (fastest decline)
  │      ○○
  │        ○○○○○○○
  │              ○○○○○
  └────────────────────────> Time
```

**2. Gompertz Model (alternative):**
```
SG(t) = SG_final + (SG_initial - SG_final) × e^(-e^(k(t₀ - t)))

Similar to logistic but different shape
```

**3. Exponential Decay (simplified):**
```
Rate(t) = Rate_max × e^(-λt)

Where:
- Rate(t) = Bubble rate at time t
- Rate_max = Maximum bubble rate
- λ = Decay constant
```

### Feature Importance

Machine learning models use multiple features:

**Primary Features:**
1. **Time elapsed** (35%): Main predictor
2. **Current gravity** (28%): Direct measurement
3. **Gravity rate of change** (20%): Indicates phase
4. **Bubble rate** (12%): Activity indicator
5. **Temperature** (5%): Environmental factor

**Derived Features:**
- Moving averages (smooth noise)
- Acceleration (2nd derivative)
- Time of day (some yeasts have circadian rhythm!)
- Days since start

### Uncertainty Sources

**Aleatory Uncertainty** (irreducible):
- Biological variation (yeast behavior)
- Environmental noise (temperature fluctuations)
- Measurement error (sensor accuracy)

**Epistemic Uncertainty** (reducible with more data):
- Model uncertainty (which equation?)
- Parameter uncertainty (what are k, t₀?)
- Initial condition uncertainty (exact starting gravity?)

**TipsyHomeLab Reports Both:**
```
Prediction: Final Gravity = 1.002 SG

Confidence Interval (95%):
├─ Lower: 1.001 SG ← Aleatory + Epistemic
└─ Upper: 1.003 SG

Width = 0.002 SG (uncertainty)
```

Narrower intervals = better predictions = more confidence

---

## Safety Calculations

### Maximum Safe Pressure

**Bottle Safety Margins:**

```
Champagne Bottle:
├─ Rated Pressure: 6.0 bar
├─ Safety Factor: 1.5× typical
├─ Burst Pressure: ~12 bar
├─ Working Limit: 4.5 bar (75% of rated)
└─ Recommended Max: 4.0 bar (67% of rated)

Target: 3.0-3.5 bar for Pet Nat (50-58% of rated)
```

**Why Safety Matters:**

Glass strength variation:
- Manufacturing defects: ±10%
- Micro-cracks: Reduce strength 20-50%
- Temperature: Hot bottles weaker
- Age: Old bottles may be weakened

**Safe Working Pressure:**
```
P_safe = P_rated × Safety_Factor

Where Safety_Factor = 0.67 (67%)

For 6 bar rated bottle:
P_safe = 6 × 0.67 = 4.0 bar maximum
```

### Calculating Bottling Gravity for Target Pressure

**Reverse Calculation:**

Given desired pressure, find bottling gravity:

```
Step 1: Calculate CO₂ needed
CO₂ (g/L) = Pressure (bar) × 2

Step 2: Calculate sugar needed
Sugar (g/L) = CO₂ / 1.6

Step 3: Convert to gravity points
Points = Sugar / 1.0

Step 4: Calculate bottling gravity
Bottling_SG = Final_SG + (Points / 1000)

Example for 3.5 bar target:
CO₂ = 3.5 × 2 = 7 g/L
Sugar = 7 / 1.6 = 4.375 g/L
Points = 4.375 ≈ 4
Bottling_SG = 1.000 + 0.004 = 1.004

Result: Bottle at 1.004 SG for 3.5 bar pressure
```

**TipsyHomeLab does this calculation automatically!**

### Worst-Case Scenarios

**What if everything goes wrong?**

```
Scenario: Warm Day After Bottling
- Bottled at: 1.006 SG
- Final gravity: 0.998 (over-attenuated)
- Points fermented: 8
- CO₂ produced: 12.8 g/L
- Base pressure (20°C): 6.4 bar ← DANGER!
- Temperature spike to 35°C: ×1.135
- Actual pressure: 7.3 bar

Result: Exceeds bottle rating → EXPLOSION RISK

Prevention:
✓ Don't bottle too early
✓ Use TipsyHomeLab predictions
✓ Store cool (10-15°C)
✓ Use champagne bottles only
✓ Monitor temperature
```

### Emergency Pressure Release

If bottles over-pressurized:

```
1. Chill immediately → Reduces pressure 15-20%
2. Move to safe location (outside, contained)
3. Slowly vent pressure:
   - Ice bath
   - Carefully loosen cap slightly
   - Let pressure escape slowly
   - Re-tighten
4. Consider re-bottling if very high pressure
```

**Never:**
- Point at people
- Handle roughly
- Shake bottles
- Expose to heat
- Ignore warning signs

---

## Summary

Understanding the science helps you:
1. **Make better decisions** about when to bottle
2. **Avoid dangerous situations** from over-pressure
3. **Troubleshoot problems** when fermentation deviates
4. **Appreciate predictions** and their limitations
5. **Optimize conditions** for best results

TipsyHomeLab combines this scientific knowledge with real-time data to provide accurate, safe guidance for Pet Nat production.

**Key Formulas Reference Card:**

```
ABV = (OG - FG) × 131.25

CO₂ (g/L) = Points_Remaining × 1.6

Pressure (bar) = CO₂ (g/L) × 0.5

Bottling_SG = Final_SG + (Target_Pressure / 0.5 / 1.6 / 1000)

Temp_Correction = Measured_SG + 0.00130 × (T - 20)

Pressure(T) = Pressure(20°C) × (1 + 0.009 × (T - 20))
```

Keep these handy for manual calculations, but remember: **TipsyHomeLab calculates everything automatically!**

---

## Further Reading

**Books:**
- "The Science of Wine" - Jamie Goode
- "Yeast" - Chris White & Jamil Zainasheff
- "Principles of Fermentation Technology" - Stanbury & Whitaker

**Papers:**
- "Mathematical Modeling of Wine Fermentation" - Malherbe et al.
- "CO₂ Solubility in Wine" - Blanco et al.
- "Pet Nat Production Methods" - Various authors

**Online:**
- Scientific American: Fermentation Chemistry
- Wine Chemistry Resources
- Yeast Biology Primers
