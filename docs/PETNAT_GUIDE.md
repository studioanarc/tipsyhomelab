# Pet Nat Production Guide

Complete guide to safely producing Pétillant Naturel (Pet Nat) using TipsyHomeLab monitoring.

---

## Table of Contents

1. [What is Pet Nat?](#what-is-pet-nat)
2. [Safety First](#safety-first)
3. [The Pet Nat Process](#the-pet-nat-process)
4. [Monitoring with TipsyHomeLab](#monitoring-with-tipsyhomelab)
5. [Bottling Window](#bottling-window)
6. [Bottle Conditioning](#bottle-conditioning)
7. [Troubleshooting](#troubleshooting)
8. [Recipes](#recipes)

---

## What is Pet Nat?

**Pétillant Naturel** (French for "naturally sparkling") is a style of sparkling wine made using the **méthode ancestrale** (ancestral method) - the oldest known method of making sparkling wine.

### How It's Different

| Method | Pet Nat (Méthode Ancestrale) | Champagne (Méthode Champenoise) |
|--------|------------------------------|----------------------------------|
| **Fermentation** | Single continuous fermentation | Two separate fermentations |
| **Sugar** | Natural grape sugars | Added sugar (dosage) |
| **Timing** | Bottle before complete | Complete, then re-ferment |
| **Disgorgement** | Usually none | Yes (remove sediment) |
| **Pressure** | Lower (2-4 bar) | Higher (5-6 bar) |
| **Complexity** | Simpler, more rustic | More refined, complex |
| **Cost** | Lower | Higher |

### Why Pet Nat?

**Advantages:**
- Traditional, natural method
- No added sugar needed
- Single fermentation (simpler)
- Unique flavor profile
- Lower pressure (safer for beginners)
- Cost-effective

**Challenges:**
- **Precise timing critical** - bottle too early = dangerous pressure, too late = flat
- Sediment in bottle (cloudy appearance)
- Less predictable than champagne method
- Requires careful monitoring

**This is where TipsyHomeLab shines**: By monitoring fermentation in real-time, we can predict the perfect bottling window with high accuracy.

---

## Safety First

### Why Safety Matters

Pet Nat creates pressure inside bottles. **Done incorrectly, bottles can explode**, causing:
- Serious injuries (glass shrapnel)
- Property damage
- Loss of entire batch

### Safety Rules

**1. Use Proper Bottles**

✅ **SAFE:**
- Champagne bottles (rated to 6+ bar)
- Belgian beer bottles (rated to 6+ bar)
- Bottles marked "sparkling wine" or "champagne"
- Heavy glass with punt (indentation) at bottom

❌ **DANGEROUS:**
- Regular wine bottles
- Thin glass bottles
- Screw-top bottles (most)
- Bottles with cracks or chips
- Bottles of unknown rating

**2. Use Proper Caps/Corks**

✅ **SAFE:**
- Champagne corks with wire cage (muselet)
- Crown caps (beer bottle caps)
- Specialized sparkling wine closures

❌ **DANGEROUS:**
- Regular wine corks (will blow out)
- Screw caps (unless specifically rated)
- Loose-fitting closures

**3. Pressure Limits**

| Closure Type | Maximum Safe Pressure |
|--------------|----------------------|
| Champagne cork + cage | 6 bar (90 PSI) |
| Crown cap | 6 bar (90 PSI) |
| Regular cork | **DO NOT USE** |

**Target Range for Pet Nat:** 2.5 - 4.0 bar (36 - 58 PSI)

**4. Storage & Handling**

- Store bottles in cool location (10-15°C / 50-59°F)
- Use bottle crate or box (contains explosions)
- Never point bottle at anyone when opening
- Wear safety glasses when handling
- Chill before opening (reduces pressure)
- Open over sink or outside

**5. Warning Signs**

Stop and reassess if you see:
- Bulging bottle caps
- Leaking closures
- Extremely fizzy fermentation
- Predicted pressure > 5 bar
- Temperature spike during conditioning

---

## The Pet Nat Process

### Overview

```
Grape Juice (or must)
     ↓
[1-2 days] Lag Phase
     ↓
[3-7 days] Active Fermentation
     ↓
[Critical] BOTTLING WINDOW ← TipsyHomeLab helps find this!
     ↓
Bottle with closures
     ↓
[2-4 weeks] Bottle Conditioning
     ↓
[Optional] Cold Crash
     ↓
Chill & Enjoy!
```

### Step-by-Step

#### 1. Start Fermentation

**Ingredients:**
- Fresh grape juice or must (no preservatives!)
- Wine yeast (or wild ferment)

**Setup:**
- Sanitize fermentation vessel
- Add juice/must
- Add yeast (or wait for wild fermentation)
- Record starting gravity (important!)
- Attach airlock
- Install TipsyHomeLab sensors

**Typical Starting Gravity:** 1.040 - 1.070 SG (depends on grape variety)

#### 2. Monitor Fermentation

**What to Watch:**
- Bubble rate (activity level)
- Specific gravity (sugar consumption)
- Temperature (should be stable)
- Fermentation phase

**TipsyHomeLab Configuration:**
```yaml
batches:
  - name: "Pet Nat Batch"
    type: petnat
    started: "2024-11-01"
    volume: 20  # liters

    # Starting values
    original_gravity: 1.055

    # Target values
    target_gravity: 1.004  # Bottle between 1.002-1.006
    target_pressure: 3.5   # bar
    bottle_volume: 750     # mL
    bottle_type: champagne

    # Safety limits
    max_pressure: 5.0      # Alert if prediction exceeds

    sensors:
      bubble_counter: "tipsylab/petnat/bubbles"
      ispindel: "ispindel/petnat"
      temperature: "tipsylab/petnat/temp"

    predictions:
      enabled: true
      model: auto
```

#### 3. Identify Bottling Window

**The Critical Question:** *When should I bottle?*

**Traditional Method (Unreliable):**
- Guess based on time
- Taste for sweetness
- Use hydrometer sporadically
- Hope for the best

**TipsyHomeLab Method (Data-Driven):**

Monitor dashboard for:
- **Current Gravity:** Should be 1.002 - 1.006 SG
- **Bubble Rate:** Slowing but still active (10-30 bubbles/min)
- **Predicted Final Gravity:** Model estimates where it will finish
- **Predicted Bottle Pressure:** Will bottles be safe?
- **Bottling Window Alert:** Notification when ready

**Ideal Bottling Gravity:**

```
Desired Bottle Pressure: 3.5 bar
Current Gravity: 1.004 SG
Predicted Final Gravity: 1.000 SG
Remaining Points: 4 points
Estimated CO2: ~6.5 g/L
Estimated Pressure: 3.2 bar ✓ SAFE
```

**Formula for Bottle Pressure:**

```
Points Remaining = (Current_SG - Final_SG) × 1000

CO2 Produced (g/L) = Points_Remaining × 1.6

Pressure (bar at 20°C) = CO2 (g/L) × 0.5
```

**Example:**
- Current SG: 1.005
- Final SG: 1.000
- Points Remaining: 5
- CO2: 5 × 1.6 = 8 g/L
- Pressure: 8 × 0.5 = 4.0 bar ✓ Safe for champagne bottles

**TipsyHomeLab automatically calculates this for you!**

#### 4. Prepare for Bottling

**24 Hours Before:**
- Sanitize bottles
- Sanitize caps/corks
- Prepare bottling equipment
- Verify pressure predictions
- Cold crash if desired (optional, settles sediment)

**Checklist:**
- [ ] Champagne bottles inspected (no cracks)
- [ ] Closures ready (corks + cages OR crown caps)
- [ ] Current gravity measured
- [ ] Pressure prediction checked (< 5 bar)
- [ ] Bottling equipment sanitized
- [ ] Labels prepared
- [ ] Storage location ready

#### 5. Bottle

**Process:**
1. Siphon into bottles, leave 1-2 inches headspace
2. Cap/cork immediately (minimize oxygen exposure)
3. If using corks: apply wire cage, twist tight
4. Label with date and batch number
5. Store upright in cool location

**Pro Tips:**
- Work quickly to minimize oxygen exposure
- Keep CO2 in solution (don't agitate)
- Fill bottles consistently (same headspace)
- Temperature affects dissolved CO2 (colder = more CO2)

#### 6. Condition

**Bottle Conditioning Phase:**

```
Days 1-7:    Active fermentation continues in bottle
Days 7-14:   Fermentation slowing, pressure building
Days 14-21:  Fermentation nearly complete
Days 21+:    Conditioning, flavors melding
```

**Monitoring:**
- Check bottles daily for leaks
- Monitor one bottle with pressure sensor (if available)
- Check cap tightness
- Observe clarity (sediment settling)

**TipsyHomeLab During Conditioning:**

Install pressure sensor on one bottle:
```yaml
sensors:
  pressure:
    topic: "tipsylab/petnat/bottle_pressure"
    alert_threshold: 5.0  # bar
```

**Temperature Management:**
- **Weeks 1-3:** Cool (15-18°C) for slow fermentation
- **Week 3+:** Cold (10-12°C) to halt fermentation
- **Never:** Warm (>20°C) - dangerous pressure buildup

#### 7. Cold Crash (Optional)

After 3-4 weeks, when fermentation is complete:

1. Move bottles to refrigerator (4°C / 39°F)
2. Keep refrigerated for 1-2 weeks
3. Yeast and sediment settle to bottom
4. Clearer wine (still cloudy compared to disgorged champagne)

#### 8. Enjoy!

**Opening Procedure:**
1. Chill bottle (reduces pressure)
2. Point away from people and valuables
3. Slowly remove wire cage (if using corks)
4. Hold cork firmly, twist bottle (not cork)
5. Let pressure release slowly
6. Pour over sink at first (sediment)
7. Serve remaining clear wine

---

## Monitoring with TipsyHomeLab

### Dashboard Example

```
┌─────────────────────────────────────────────────┐
│  🍾 Pet Nat "Spring Blossom" - Day 6            │
├─────────────────────────────────────────────────┤
│                                                  │
│  Status: APPROACHING BOTTLING WINDOW            │
│                                                  │
│  Current Readings:                              │
│  • Gravity: 1.006 SG (started at 1.055)        │
│  • Temperature: 17.2°C                          │
│  • Bubble Rate: 22/min                          │
│                                                  │
│  Predictions:                                   │
│  • Final Gravity: 1.001 SG (±0.001)            │
│  • Bottle Pressure: 2.8 bar (±0.4)             │
│  • Bottling Window: OPEN (next 48 hours)       │
│  • Completion: Nov 20 (in 6 days)              │
│                                                  │
│  Safety Check:                                  │
│  ✓ Predicted pressure safe (< 5.0 bar)         │
│  ✓ Temperature stable                           │
│  ✓ No stuck fermentation detected              │
│                                                  │
│  💡 Recommendation: BOTTLE TOMORROW             │
│                                                  │
│  [Bottle Now] [Remind Me Tomorrow] [Details]   │
└─────────────────────────────────────────────────┘
```

### Key Metrics

**1. Attenuation Progress**
```
Starting Gravity: 1.055
Current Gravity:  1.006
Final Gravity:    1.001 (predicted)

Attenuation = (1.055 - 1.006) / (1.055 - 1.000) × 100% = 89%
```

**2. Points Remaining**
```
Current - Final = 1.006 - 1.001 = 0.005 = 5 points

This determines bottle carbonation!
```

**3. Estimated CO2**
```
CO2 (g/L) = Points × 1.6 = 5 × 1.6 = 8 g/L

For comparison:
- Still wine: < 2 g/L
- Pet Nat: 6-10 g/L
- Champagne: 10-12 g/L
- Beer: 4-8 g/L
```

**4. Bottle Pressure**
```
Pressure = CO2 × 0.5 = 8 × 0.5 = 4.0 bar at 20°C

Temperature affects pressure:
- At 10°C: ~3.2 bar
- At 20°C: ~4.0 bar
- At 30°C: ~4.8 bar
```

### Automation Examples

**Alert When Bottling Window Opens:**

```yaml
automation:
  - alias: "Pet Nat Ready to Bottle"
    trigger:
      - platform: state
        entity_id: binary_sensor.tipsylab_petnat_bottling_window
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "🍾 Pet Nat Ready!"
          message: >
            Your Pet Nat batch is ready to bottle!
            Current gravity: {{ states('sensor.tipsylab_petnat_gravity') }}
            Predicted pressure: {{ states('sensor.tipsylab_petnat_predicted_pressure') }} bar
          data:
            priority: high
```

**Alert if Pressure Too High:**

```yaml
automation:
  - alias: "Pet Nat Pressure Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.tipsylab_petnat_predicted_pressure
        above: 5.0
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ URGENT: High Pressure Warning"
          message: >
            Predicted bottle pressure exceeds safe limit!
            Predicted: {{ states('sensor.tipsylab_petnat_predicted_pressure') }} bar
            BOTTLE IMMEDIATELY or risk dangerous over-carbonation!
          data:
            priority: emergency
```

---

## Bottling Window

### Finding the Sweet Spot

**Goal:** Bottle when enough sugar remains for carbonation, but not so much to over-carbonate.

```
Fermentation Progress
│
│  Too Early        Perfect        Too Late
│  ↓                ↓              ↓
│  ●────────────────●──────────────●
│  1.010           1.004          0.998
│
│  Result:          Result:        Result:
│  Over-carbonated  Perfect 3.5bar Under-carbonated
│  >6 bar           Nice fizz      Slightly sparkling
│  DANGEROUS!       ✓ SAFE         Disappointing
```

### Calculating Bottling Gravity

**Formula:**
```
Bottling_SG = Final_SG + (Desired_Pressure / 0.5 / 1.6 / 1000)
```

**Example:**
```
Final SG: 1.000 (predicted)
Desired Pressure: 3.5 bar

Points Needed = 3.5 / 0.5 / 1.6 = 4.375 ≈ 4 points

Bottling SG = 1.000 + 0.004 = 1.004 ✓
```

**TipsyHomeLab calculates this automatically!**

### Temperature Compensation

Warmer temperatures = more pressure

```
Pressure at Different Temperatures (for 8 g/L CO2):

10°C: 3.2 bar
15°C: 3.6 bar
20°C: 4.0 bar
25°C: 4.4 bar
30°C: 4.8 bar
```

**Implications:**
- Bottle and condition in cool environment
- Summer batches need extra care
- Cold crash before opening reduces pressure

---

## Bottle Conditioning

### Timeline

**Week 1: Active Fermentation**
- Yeast consuming remaining sugar
- CO2 production
- Pressure building
- Monitor daily

**Week 2-3: Completion**
- Fermentation slowing/stopping
- Pressure stabilizing
- Sediment beginning to settle
- Check for leaks

**Week 3+: Conditioning**
- Flavors melding
- Sediment settling
- Can drink but better with age
- Safe to cold crash

**Month 3+: Mature**
- Optimal flavor development
- Well-carbonated
- Sediment compact
- Best drinking window

### Monitoring Conditioning

**Visual Inspection:**
- Check caps/corks daily (tight?)
- Look for leaks
- Observe clarity improving
- Sediment settling

**Pressure Monitoring:**
Install sensor on one "sacrifice" bottle:

```python
# Example: Monitor bottle pressure
if bottle_pressure > 5.5:
    send_alert("DANGER: High pressure!")
    recommend_action("Cold crash immediately")
elif bottle_pressure > 5.0:
    send_alert("Warning: Approaching max pressure")
    recommend_action("Move to cooler location")
elif bottle_pressure > 4.5:
    send_alert("Info: Slightly high pressure")
elif 2.5 <= bottle_pressure <= 4.5:
    send_alert("Perfect carbonation range!")
else:
    send_alert("Info: Under-carbonated")
```

---

## Troubleshooting

### Over-Carbonation

**Symptoms:**
- Gushing when opened
- Bulging caps
- Very high pressure
- Explosive opening

**Causes:**
- Bottled too early (too much sugar)
- Temperature too high during conditioning
- Fermentation not slowed properly

**Solutions:**
- **Immediate:** Cold crash all bottles
- **Short-term:** Slowly release pressure (vent caps)
- **Long-term:** Improve bottling timing prediction
- **Emergency:** Carefully open and re-bottle with less headspace

**Prevention:**
- Use TipsyHomeLab predictions
- Bottle at correct gravity
- Condition in cool environment
- Monitor pressure if possible

### Under-Carbonation

**Symptoms:**
- Flat or barely sparkling
- Low pressure when opening
- Disappointing fizz

**Causes:**
- Bottled too late (not enough sugar)
- Temperature too low during conditioning
- Yeast died before completing
- Bottle leak

**Solutions:**
- **Cannot fix** once bottled (sugar consumed)
- Enjoy as lightly sparkling
- Add small amount of sugar (risky!)

**Prevention:**
- Use TipsyHomeLab predictions
- Don't bottle too late
- Ensure active yeast at bottling
- Check closures

### Stuck Fermentation in Bottle

**Symptoms:**
- Fermentation stops in bottle
- Under-carbonated result
- Sediment but no pressure

**Causes:**
- Yeast stressed or dead
- Temperature shock
- Lack of nutrients
- Too much SO2

**Solutions:**
- Gently warm bottles
- Wait longer (yeast may restart)
- Cannot add more yeast once bottled

**Prevention:**
- Healthy yeast at bottling
- Adequate yeast nutrients
- Minimize SO2 before bottling
- Gradual temperature changes

### Bottles Exploding

**Symptoms:**
- Bottles breaking (DANGER!)
- Glass everywhere
- Loss of batch

**Causes:**
- Wrong bottle type
- Over-carbonation
- Temperature spike
- Bottle defect

**Immediate Actions:**
1. Move remaining bottles to cold storage
2. Check all bottles for damage
3. Carefully vent some pressure if safe
4. Consider re-bottling remaining

**Prevention:**
- **Use proper bottles!**
- Monitor pressure predictions
- Cool conditioning environment
- Inspect bottles before use

---

## Recipes

### Basic Pet Nat

**Ingredients:**
- 20L grape juice (white grapes, no preservatives)
- Wine yeast (EC-1118 or Champagne yeast)
- Yeast nutrient

**Process:**
1. Starting gravity: ~1.050
2. Ferment at 16-18°C
3. Bottle at 1.004 SG
4. Condition for 3-4 weeks

**Expected Result:**
- ABV: ~6.5%
- Pressure: ~3.5 bar
- Light, crisp, fruity

### Apple Pet Nat (Pét Nat Cidre)

**Ingredients:**
- 20L fresh apple juice
- Champagne yeast
- Yeast nutrient (optional)

**Process:**
1. Starting gravity: 1.045-1.050
2. Ferment at 15-17°C
3. Bottle at 1.003-1.005
4. Condition for 3-4 weeks

**Expected Result:**
- ABV: 5-6%
- Pressure: 3-4 bar
- Crisp, apple forward

### Rosé Pet Nat

**Ingredients:**
- 20L rosé grape juice or must
- Wild fermentation OR wine yeast
- Yeast nutrient

**Process:**
1. Starting gravity: 1.055-1.060
2. Ferment at 17-19°C
3. Bottle at 1.004-1.006
4. Condition for 4 weeks

**Expected Result:**
- ABV: 6.5-7.5%
- Pressure: 3-4 bar
- Fruity, slightly funky

---

## Summary

Pet Nat is a beautiful, traditional method of creating sparkling wine. The key challenge - finding the perfect bottling moment - is exactly what TipsyHomeLab solves through real-time monitoring and machine learning predictions.

**Key Takeaways:**
1. **Safety first** - Use proper bottles and monitor pressure
2. **Timing is critical** - Too early = dangerous, too late = flat
3. **Monitor continuously** - TipsyHomeLab tracks and predicts
4. **Bottle at 1.002-1.006 SG** - For 2.5-4 bar pressure
5. **Condition cool** - 15-18°C for 3-4 weeks
6. **Enjoy responsibly** - Chill before opening, point away from people

With TipsyHomeLab, you can confidently produce safe, delicious Pet Nat every time!

---

**Santé! 🥂**
