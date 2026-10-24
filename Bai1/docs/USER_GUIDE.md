# User Guide — Triangle Solver

## 1. Open the application

You need two terminals, both starting from the `Bai1` folder.

**Terminal 1 — backend**

```powershell
.\.venv\Scripts\python.exe -m uvicorn triangle_knowledge_base.app.api.main:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — frontend**

```powershell
cd frontend
npm install      # first time only
npm run dev
```

Then open **http://127.0.0.1:5173**. The first-time setup is in the [README](../README.md).


## 2. Enter what you know

- Type values into **Sides** (a, b, c) and **Angles** (A, B, C, in degrees). Side *a* is opposite angle *A*, and so on.
- Leave a field empty if you don't know it. Don't type 0 for an unknown value.
- Decimals work with a point or a comma: `4.5` or `4,5`.
- For area, semiperimeter, altitudes and the two radii, open **Advanced parameters**.
- If a value is not allowed, a red message appears under the field (for example "Angles must be between 0° and 180°."). Solving stays disabled until you fix it.

## 3. Choose what to find

- Under **Find**, click the chips for the values you want. A selected chip turns blue; click it again to deselect it.
- Hover a chip to see its full name.
- **Select all** and **Clear** change every chip at once.

## 4. Solve

- **Solve selected** asks the backend for the chosen values.
- **Calculate all possible** asks for every value the 46 rules can derive from your facts.

Nothing is calculated while you type. You always press a button.

## 5. Read the results

- The colored box at the top shows the solver status:
  - green **Solved**
  - amber **Unresolved**
  - red **Invalid** or **Inconsistent**
- Each requested value appears as an item with a badge:
  - **Given** — you entered it.
  - **Inferred** — the system derived it. These values are shown in blue.
  - **Unresolved** — it could not be derived.
- Values are rounded to 4 decimals for display only. Calculations use full precision.
- **Intermediate values also derived** lists values the solver found along the way.


## 6. See how a value was derived

- Open **Solution steps**. Each step shows:
  - the rule ID (e.g. R20);
  - its relation group (e.g. Q05 · Heron's formula);
  - the formula;
  - the input values used;
  - the resulting value.
- Click a result item to see only the steps that value depends on. Switch to **Full trace** to see the complete inference sequence.
- Click a step to highlight it. Its output is highlighted on the triangle, with its inputs in a lighter blue.


## 7. Explore the triangle

The triangle is drawn to scale once the solver knows all three sides.

- Hover or tab to a side or angle to see its name, its value, and whether it was given or inferred.
- Click it, or press Enter, to select it.
- Selecting a result also highlights it on the drawing:
  - an altitude draws its line;
  - **S** shades the interior;
  - **r** and **R** draw the incircle and circumcircle.
- The buttons at the top right of the triangle card:
  - ↺ clears the highlight;
  - the tag button hides or shows labels;
  - the arrows enlarge the drawing.
- If only the three angles are known, the shape is drawn **scale-normalized**: correct proportions, unknown size.

## 8. Example problems

Use **Load example…** to fill in a ready-made problem:

| Example | Shows |
|---|---|
| 3-4-5 triangle (SSS) | A solved problem |
| SAS: b = 3, c = 4, A = 90° | Two sides and the included angle |
| ASA/AAS: A = 50°, B = 60°, c = 10 | Two angles and a side |
| Insufficient information | Unresolved |
| Invalid triangle 1, 2, 3 | Invalid |

Loading an example fills the fields and targets but does not solve. Press **Solve selected** when you are ready.

## 9. Reset

**Reset** in the header clears all inputs, targets and results.

## 10. Errors and unresolved states

| You see | Meaning | What to do |
|---|---|---|
| **Unresolved** | The rules cannot derive the value from your facts. This does not mean the triangle is impossible. | Add another known value |
| **Ambiguous** (on the drawing) | Two sides and a non-included angle may fit two different triangles. The solver does not choose one. | Give the included angle or the third side |
| **Invalid** | The values cannot form a triangle, e.g. 1, 2, 3 breaks the triangle inequality | Correct the values |
| **Inconsistent** | Each value is fine alone, but they contradict each other. The box names the rule, e.g. "Q05/R20 Heron: S=7, expected 6". | Remove or correct one of the conflicting values |
| **Inputs changed** banner | Results belong to earlier inputs | Solve again |
| "Cannot reach the solver backend" | The FastAPI server is not running | Start it, then press **Retry** |
