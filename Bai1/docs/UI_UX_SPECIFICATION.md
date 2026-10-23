# UI/UX Specification — Triangle Solver

This describes the interface as implemented in `frontend/`, not the original proposal.

## Information architecture

A single page with no routing.

```
Header: logo · "Triangle Solver" · "Computational Network" | Reset · Help (dialog)
Main
├─ Left (≈35%): Known parameters card
│   ├─ Example selector ("Load example…")
│   ├─ Sides a b c · Angles A B C (°)
│   ├─ Advanced parameters (accordion, collapsed): S p ha hb hc r R
│   ├─ Find: 13 target chips · Select all · Clear
│   └─ Solve selected · Calculate all possible
└─ Right (≈65%)
    ├─ Triangle card: state badge · Reset view · Labels toggle · Expand · SVG · inspection line
    └─ Results card: status badge · status box · stale banner · result items ·
       intermediate values · Solution steps (accordion, collapsed)
```

## Layout and responsive rules

| Viewport | Layout |
|---|---|
| ≥ 1024 px (`lg`) | Two columns, `35fr / 65fr`, max width 1400 px |
| 640–1023 px | Single column: inputs, then triangle, then results; solve buttons side by side |
| < 640 px | Single column; solve buttons stacked full width; Expand button hidden; header subtitle hidden |

- No horizontal scrolling at any width. E2E-06 checks `scrollWidth` at 1440, 768 and 390 px.
- The SVG viewBox follows the container's measured width (ResizeObserver). Label font sizes therefore stay in real pixels.
- Aspect ratio is 0.63 on wide screens and 0.85 below 500 px. Expand switches to 0.8.
- Touch targets are at least 36 px tall: chips are 36 px, buttons 40 px.

## Visual design

- Neutral slate palette, defined as Tailwind v4 `@theme` tokens in `src/index.css`.
- Primary blue `#2563eb` marks calculated values, selections and focus rings.
- Green, amber and red appear only in status boxes and badges.
- Inter Variable (bundled with `@fontsource-variable`) for UI text. A serif italic math face (Cambria Math / STIX fallback) for variable symbols. Subscripts are rendered as `h<sub>a</sub>`.
- Cards use a 1 px border, `rounded-xl` corners and the `shadow-xs` shadow. There are no gradients apart from the faint dot grid behind the drawing.

## Components

The shadcn/ui-style primitives in `src/components/ui/` are built on the `radix-ui` package:

- Button
- Input
- Card
- Accordion
- Tooltip
- Badge
- Dialog
- Separator

Feature components:

| Component | Role |
|---|---|
| `InputPanel` | Inputs, advanced accordion, examples, target chips, solve actions |
| `TriangleView` | SVG visualization, its controls and the inspection line |
| `ResultsPanel` | Status, result items, intermediate values, solution steps |
| `Sym` | Math notation for a variable |

## Interaction behavior

**Inputs**
- Text inputs use `inputMode="decimal"`, so mobile shows a numeric keypad.
- Empty means unknown. Zero is never substituted.
- A comma is accepted as the decimal separator.
- Invalid entries get an inline message and `aria-invalid`.
- While any field is invalid, both solve buttons are disabled.

**Solving**
- Only a button press triggers inference. Typing never calls the backend.
- While a request is pending, both buttons show a spinner and are disabled.
- A newer request aborts the previous one, and responses from superseded requests are ignored.

**Calculate all possible** sends all 13 variables as goals. The engine already runs until nothing new can be derived, so no backend change was needed. The status box then reads, for example, "Calculated everything the knowledge base can derive: N of 13 values known."

**Stale results** — editing any fact after a solve:
- dims the results;
- shows the banner "Inputs changed since this result";
- replaces the drawing with "Inputs changed. Solve again to update the triangle.";
- clears the current selection.

Loading an example resets the workspace and fills the fields. It does not solve.

**Selecting a result** (a result item, an intermediate-value chip, or a side or angle in the SVG):
- highlights the geometry;
- opens Solution steps;
- filters the steps to the dependency chain of that value ("Steps for X" / "Full trace").

The chain is rebuilt from each step's recorded `inputs`, which the backend trace provides exactly.

**Selecting a step** highlights its output in the primary style and its inputs in the secondary style.

## Visual states

Visual state is computed separately from solver status (`lib/geometry.ts › visualState`).

| State | When | Rendering |
|---|---|---|
| Placeholder | No result, or no unique shape derivable | Grey dashed triangle + "Enter sufficient parameters to construct a triangle." |
| Placeholder (stale) | Facts edited after solve | Same, with the stale message |
| Constructed | Response facts contain a, b, c (any status except INVALID/INCONSISTENT) | Accurate triangle, "To scale" badge |
| Constructed, normalized | A, B, C known but no side | Shape from sides ∝ sin A, sin B, sin C; "Scale-normalized: shape only" badge; side values hidden |
| Ambiguous | Two sides + an angle opposite one of them, included angle unknown (SSA) | Amber dashed placeholder, explanation; no configuration chosen |
| Invalid | Status INVALID | Red dashed placeholder |
| Inconsistent | Status INCONSISTENT | Red dashed placeholder |

UNRESOLVED does not imply invalid. If the backend derived all three sides, the triangle is drawn even when other goals are missing.

## Mathematical visualization

- All values come from the backend. Frontend geometry only positions SVG elements.
- Vertex placement: B = (0, 0), C = (a, 0), and A from the two-circle intersection:
  - x = (c² + a² − b²) / 2a
  - y = √(c² − x²)
- Scaling is uniform to fit the box minus a 40–56 px margin, centered, with y flipped.
- When the circumcircle is shown, its bounds join the fit, so the circle never clips.
- Labels:
  - Vertex labels are pushed away from the centroid.
  - Side labels sit at each midpoint, offset outward.
  - Angle values sit on the angle bisector.
  - Every label has a 5 px card-colored halo, so it stays readable where it crosses a line.
- Highlights:

  | Selected | Highlight |
  |---|---|
  | a, b, c | That side is drawn thicker in blue |
  | A, B, C | Filled angle arc and enlarged vertex |
  | ha, hb, hc | Dashed altitude to the foot, plus a dashed extension of the base when the foot falls outside it (obtuse triangles) |
  | S | Interior fill |
  | p | All three sides |
  | r | Incircle |
  | R | Circumcircle |

## Accessibility

- Semantic structure: `header`, `main`, `aside`, and `section` regions labelled by their headings. Inputs are grouped in `fieldset`/`legend`.
- Every input has an associated label, and its accessible name spells the variable out ("Altitude to a").
- Target chips and result items are buttons with `aria-pressed`.
- SVG sides and angles are focusable (`tabIndex=0`, `role="button"`) and activate with Enter or Space. Focusing one shows its description in a polite live region.
- The SVG has a `<desc>` summarizing all sides and angles, and whether each is given or inferred.
- Status boxes use `role="status"`; API errors use `role="alert"`.
- Known versus inferred is shown with text as well as color: "Given" / "Inferred" / "Unresolved" badges with icons, and dotted underlines on inferred SVG labels.
- Visible focus rings appear on all controls.
- `prefers-reduced-motion` disables transitions and the spinner.
