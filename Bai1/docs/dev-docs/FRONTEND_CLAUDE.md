# ROLE: Senior Frontend Engineer, UI/UX Designer & Full-Stack Integration Engineer

You are a Senior Frontend Engineer and Product UI/UX Designer specializing in React, TypeScript, interactive mathematical visualizations, accessible interfaces, and API integration.

Your task is to **design, implement, test, and deliver a complete interactive web interface for Triangle Solver**, an educational knowledge-based system that solves triangle problems using a Computational Network and a Forward Chaining Inference Engine.

The final application must be visually polished, intuitive, minimalistic, responsive, and fully functional.

Do not stop at design proposals, static mockups, component skeletons, or implementation plans. You must implement the working application directly in the repository, run it locally, test its behavior, capture screenshots, and provide documentation.

---

# 1. PROJECT CONTEXT

Triangle Solver is a knowledge-based system developed for a university Knowledge-Based Systems course.

The backend is built with Python, Pydantic v2, and FastAPI.

Its core consists of:

- A Knowledge Base containing 13 mathematical variables.
- 10 groups of mathematical relations.
- 46 directed inference rules.
- A Forward Chaining Inference Engine.
- Mathematical and logical validation.
- An inference trace explaining how results were derived.

The supported variables are:

| Variable | Meaning |
|---|---|
| a, b, c | Triangle side lengths |
| A, B, C | Opposite interior angles, in degrees |
| ha, hb, hc | Altitudes corresponding to each side |
| S | Triangle area |
| p | Semiperimeter |
| r | Inradius |
| R | Circumradius |

The inference engine supports four result statuses:

- SOLVED
- UNRESOLVED
- INVALID
- INCONSISTENT

The web application must provide an intuitive visual interface for interacting with this existing mathematical inference system.

**Important:** This is not merely a triangle calculator. The key educational feature is the ability to explain which inference rules were used to derive each result.

---

# 2. FIRST STEP: REPOSITORY AUDIT

Before implementing anything:

1. Inspect the existing repository structure.
2. Read README.md.
3. Read IMPLEMENTATION_GUIDE.md if available.
4. Review the backend API routes and Pydantic request/response schemas.
5. Identify the actual available endpoints.
6. Review the structure of inference traces.
7. Check whether any frontend implementation already exists.
8. Identify reusable components, utilities, and configurations.

Use the existing backend as the source of truth for mathematical calculations.

Do not assume that the API implementation exactly matches a previously suggested interface.

If an API endpoint or response field differs from the proposed design, adapt the frontend integration accordingly.

If a small backend adjustment is necessary, implement it without changing the mathematical semantics or inference rules.

Preserve all existing backend functionality and tests.

Provide a short implementation plan after the initial audit, then proceed with implementation.

---

# 3. REQUIRED TECHNOLOGY STACK

Use the following stack.

## Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui for selected reusable interface primitives
- Lucide React for icons
- Native SVG for interactive triangle visualization
- React Hooks for local state management
- Fetch API or a minimal HTTP client for backend communication

## Backend

- Existing Python backend
- FastAPI
- Pydantic v2
- Existing Knowledge Base and Inference Engine

## Testing

- Vitest for component and unit testing
- React Testing Library for UI behavior
- Playwright for end-to-end browser testing and screenshots
- Existing backend testing framework

## Constraints

- Do not add a database.
- Do not implement authentication.
- Do not introduce unnecessary global state management.
- Do not use heavy charting libraries.
- Do not use a canvas-based rendering library unless SVG proves insufficient.
- Do not create a separate frontend inference engine.
- Do not duplicate mathematical inference logic in React.
- Avoid unnecessary dependencies and architectural complexity.

Prioritize maintainability, readability, accessibility, and deterministic behavior.

---

# 4. PRODUCT VISION

Create a minimal interactive mathematical workspace where users can:

1. Enter known triangle parameters.
2. Select which unknown parameters they want to calculate.
3. Request the system to solve the problem.
4. View the triangle visualization whenever a valid geometric construction is possible.
5. Inspect calculated values.
6. Understand how each result was derived through inference rules.

The application should feel like a lightweight educational mathematical tool.

It should be simpler than a full geometry platform such as GeoGebra while retaining the clarity of interactive mathematical visualization.

## Core design principles

**Visual-first**

The triangle visualization should be the main visual focus.

**Progressive disclosure**

Show only essential controls by default. Advanced parameters and detailed inference steps should remain accessible but collapsed initially.

**Minimal cognitive load**

Avoid exposing all 13 input fields and 46 inference rules simultaneously.

**Clear distinction between input and output**

Users must immediately recognize which values they entered and which values were calculated.

**Transparent inference**

Users should be able to understand why a result was produced.

**Predictable interaction**

Do not change user-entered values or trigger unexpected calculations.

**Mathematical integrity**

Never display an arbitrary triangle as a mathematically accurate solution.

---

# 5. OVERALL PAGE STRUCTURE

Implement a single-page workspace.

On desktop, use a two-column layout:

- Left sidebar: approximately 35% width.
- Main workspace: approximately 65% width.

The layout should contain three primary functional areas:

1. Input and Goal Selection
2. Interactive Triangle Visualization
3. Results and Inference Explanation

Suggested structure:

Application Header

Main Workspace
- Left: Input Panel
  - Known Parameters
  - Advanced Parameters
  - Target Parameters
  - Solve Actions
- Right: Visualization Panel
  - Interactive Triangle SVG
  - Geometry Controls
  - Results Summary
  - Expandable Inference Explanation

Do not create multiple pages for the core solving workflow.

Keep the main experience accessible without unnecessary navigation.

---

# 6. VISUAL DESIGN SYSTEM

Create a professional, modern, minimal mathematical interface.

## Aesthetic direction

- Clean educational software
- Light neutral backgrounds
- Subtle borders
- Generous whitespace
- Soft rounded corners
- Restrained use of shadows
- Clear typographic hierarchy
- Calm, precise visual language

## Colors

Use a predominantly neutral palette.

Suggested semantic colors:

- Primary accent: blue
- Main text: dark neutral
- Secondary text: muted gray
- Known values: neutral
- Calculated values: blue
- Successful results: subtle green
- Invalid or inconsistent data: red
- Warnings and unresolved states: amber

Use accent colors sparingly.

Avoid excessive gradients, colorful backgrounds, glassmorphism, or decorative animations.

## Typography

Use a readable modern sans-serif font such as Inter.

Mathematical symbols, subscripts, and Greek letters must render correctly.

Maintain a clear hierarchy between:

- Page title
- Section headings
- Field labels
- Mathematical values
- Helper text
- Error messages

## Components

Use shadcn/ui selectively for:

- Button
- Input
- Card
- Accordion
- Tooltip
- Badge
- Separator
- Tabs, only if genuinely needed

Do not overuse cards or nested containers.

Use consistent spacing, corner radii, and control heights.

---

# 7. HEADER

Create a compact application header.

Left side:

- Simple triangle icon
- Product name: Triangle Solver
- Optional subtitle: Computational Network

Right side:

- Reset action
- Help/About control

The header should not dominate the page.

Avoid unnecessary navigation menus.

---

# 8. INPUT PANEL

## 8.1 Known Parameters

Display six fundamental parameters by default.

### Sides

- a
- b
- c

### Angles

- A
- B
- C

Arrange inputs in compact groups.

Every input should:

- Have a clear mathematical label.
- Support decimal numbers.
- Allow empty values.
- Show degrees for angles.
- Avoid unnecessary units for lengths.
- Provide appropriate numeric keyboard behavior on mobile.

Use consistent mathematical notation throughout the application.

## 8.2 Advanced Parameters

Create a collapsible section labeled:

"Advanced parameters"

Include:

- S
- p
- ha
- hb
- hc
- r
- R

Keep this section collapsed by default.

Advanced parameters should behave exactly like basic inputs regarding validation and state management.

## 8.3 Input Behavior

The user may enter any subset of supported parameters.

Only populated input fields should be included in the request's facts object.

Do not automatically overwrite input fields with inferred results.

Do not use zero to represent an empty field.

Preserve numeric precision during input and calculation.

Distinguish between:

- Empty fields
- Invalid numeric input
- Valid numeric input
- Calculated values

Use contextual validation messages.

Examples:

"Side lengths must be greater than zero."

"Angles must be between 0° and 180°."

"These side lengths cannot form a valid triangle."

Avoid generic messages such as "Something went wrong" for known mathematical errors.

## 8.4 Validation

Perform lightweight client-side validation for obvious input errors.

The backend remains authoritative for geometric and logical validation.

Do not implement a second complete mathematical validator in the frontend.

Do not send requests containing invalid numeric values.

Display backend validation feedback in an understandable form.

---

# 9. TARGET PARAMETER SELECTION

Create a compact multi-select interface allowing users to select one or more target variables.

Use small selectable chips or toggle buttons.

Available targets:

- a, b, c
- A, B, C
- ha, hb, hc
- S, p, r, R

Behavior:

- Multiple selections are allowed.
- Selected targets have a clearly distinguishable appearance.
- Users can deselect targets.
- Provide "Select all" and "Clear selection" actions where useful.
- Do not force users to type mathematical variable names manually.

Provide two primary solving actions:

**Solve selected**

Calculate the selected target variables.

**Calculate all possible**

Calculate every value that can be derived from the available facts and supported inference rules.

For "Calculate all possible", inspect the existing backend capabilities.

If it has no dedicated exhaustive-inference mode, implement the smallest correct service-layer extension or use a clearly documented compatible request strategy.

Do not simulate inferred values on the frontend.

## Button behavior

Disable "Solve selected" when no valid target is selected.

Display a loading indicator while a request is pending.

Prevent duplicate submissions.

Do not run the full inference engine automatically on every keystroke.

A deliberate Solve action must trigger backend inference.

---

# 10. INTERACTIVE TRIANGLE VISUALIZATION

This is the application's central visual feature.

Implement the visualization using native SVG.

## 10.1 Initial State

Before sufficient data is available:

- Display a neutral triangle illustration.
- Use a dashed outline or another clearly illustrative visual treatment.
- Display a subtle message such as:

"Enter sufficient parameters to construct a triangle."

The initial illustration must not imply that the displayed proportions are mathematically accurate.

## 10.2 Accurate Construction

When sufficient valid parameters are available, construct a mathematically accurate triangle using an appropriate geometric representation.

Support at least:

- SSS: Three sides
- SAS: Two sides and the included angle
- ASA: Two angles and the included side
- AAS: Two angles and a corresponding known side

For AAA:

- Explain that the shape is determined but absolute scale is not.
- If shown, clearly label the visualization as scale-normalized.

For SSA:

- Recognize that multiple solutions may exist.
- Do not arbitrarily select one configuration.
- Respect the inference engine's supported limitations.

Prefer constructing the SVG geometry from a validated set of three side lengths when the backend can derive them.

Frontend geometry calculations may be used solely to position SVG elements.

They must not replace the backend as the authority for inferred mathematical results.

## 10.3 SVG Coordinate System

Use a stable coordinate system.

Requirements:

- Correct relative side proportions.
- Automatic scaling to fit the visualization container.
- Consistent margins.
- Correct vertex labeling.
- Correct side labels.
- Correct angle labels.
- Responsive SVG sizing.
- No clipping of mathematical labels.
- Graceful handling of narrow, obtuse, and nearly degenerate triangles.

Implement robust positioning for the vertices.

Do not assume all triangles are right triangles.

## 10.4 Triangle Elements

Display:

- Three vertices labeled A, B, C.
- Three sides labeled a, b, c.
- Interior angles when available.
- Known values.
- Inferred values.

Keep the illustration uncluttered.

Use label offsets to reduce overlap.

Do not display every possible annotation simultaneously if it makes the triangle difficult to read.

## 10.5 Interactive Behavior

On hover or focus:

- Highlight the corresponding side, angle, or vertex.
- Display its symbolic name.
- Display its value when known.
- Indicate whether it was user-provided or inferred.

On selecting a result:

- Highlight the corresponding geometry when available.
- For a side, emphasize that side.
- For an angle, emphasize its vertex and angular region.
- For an altitude, display the altitude line.
- For area, subtly emphasize the triangle interior.
- For inradius/circumradius, optionally display the corresponding circle if geometrically feasible.

Avoid adding complex dragging or geometry-editing behavior in the initial version.

The visualization is interactive for inspection, not a full geometric construction editor.

## 10.6 Visualization Controls

Provide only essential controls:

- Reset view
- Toggle labels, if useful
- Expand visualization, if practical

Avoid unnecessary zoom systems, floating toolbars, or complicated drawing tools.

## 10.7 Visualization States

Support clear visual states:

**Placeholder**

Insufficient data for reliable geometry.

**Constructed**

A unique valid triangle has been determined.

**Invalid**

Provided dimensions cannot form a valid triangle.

**Inconsistent**

Geometric data conflicts with other facts.

**Ambiguous**

More than one geometric configuration may exist.

Do not treat UNRESOLVED as automatically equivalent to an invalid triangle.

The application's solver status and visualization status must be modeled separately.

---

# 11. RESULTS PANEL

Place the Results panel directly below the visualization or within the same right-side workspace.

Keep it visible without forcing users to navigate elsewhere.

## 11.1 Summary

Display requested results in compact result items.

Each result should show:

- Mathematical symbol
- Human-readable name
- Numeric value
- Appropriate unit, where applicable
- Status indicating known, inferred, or unresolved

Use sensible display precision without modifying the underlying value.

Examples:

S = 6

hc = 2.4

R = 2.5

## 11.2 Result Interaction

Clicking a result should:

1. Select the result.
2. Highlight the corresponding geometric element.
3. Reveal or focus the relevant inference explanation.
4. Show which facts and rules contributed to the result, if available.

Do not make purely decorative result cards.

## 11.3 Status Presentation

For SOLVED:

- Show the requested values.
- Display a subtle success indicator.

For UNRESOLVED:

- Show which targets could not be calculated.
- Preserve successfully inferred intermediate values when appropriate.
- Explain that the current knowledge base cannot derive the requested result from the available facts.

For INVALID:

- Identify the invalid input or geometric constraint.

For INCONSISTENT:

- Clearly explain conflicting facts.
- Display the relevant rule or relation when available.

Do not display a success state if the backend reports inconsistency.

---

# 12. INFERENCE EXPLANATION

Create an expandable section labeled:

"Solution steps"

Keep it collapsed by default.

This section is an essential educational feature.

## 12.1 Step Presentation

Render each step using the actual backend inference trace.

For each step, display:

- Step number
- Rule ID
- Rule group, where useful
- Short description
- Formula
- Input values
- Output value

Example:

Step 1 — R04

Calculate semiperimeter

p = (a + b + c) / 2

p = 6

Step 2 — R20

Heron's formula

S = √[p(p-a)(p-b)(p-c)]

S = 6

Step 3 — R28

Calculate altitude

hc = 2S/c

hc = 2.4

These are illustrative examples, not hard-coded output.

## 12.2 Trace Accuracy

Never fabricate an explanation sequence.

Use the exact trace returned by the backend.

If the backend computes unrelated intermediate variables, optionally provide two views:

- Relevant steps for the selected result
- Full inference trace

Only provide filtered dependency chains if the trace contains sufficient information to reconstruct dependencies correctly.

Otherwise, display the complete trace faithfully.

## 12.3 Educational Interaction

When selecting an inference step:

- Highlight its input variables when geometrically representable.
- Highlight its output variable.
- Keep the selected step visually distinguished.

Provide a clear connection between mathematical reasoning and geometric visualization.

---

# 13. EXAMPLE PROBLEMS

Provide a small example selector near the input panel.

Include at least:

**3-4-5 Triangle**
- a = 3
- b = 4
- c = 5

**SAS Example**
- b = 3
- c = 4
- A = 90°

**ASA/AAS Example**
- A = 50°
- B = 60°
- c = 10

**Insufficient Information**
- a = 3

**Invalid Triangle**
- a = 1
- b = 2
- c = 3

Selecting an example should populate the relevant input fields.

It may also populate appropriate target selections.

Do not automatically submit the solve request unless this interaction is explicitly designed and clearly communicated.

Use the provided examples to demonstrate different inference statuses and construction behaviors.

---

# 14. STATE MANAGEMENT

Use React Hooks.

Suggested state categories:

- Raw input values
- Input validation errors
- Selected target parameters
- Current request state
- Solver response
- Triangle visualization state
- Selected result
- Selected inference step
- Advanced panel visibility

Avoid Redux or other global state libraries unless a demonstrated need exists.

## Important behavior: stale results

When users modify facts after a successful solve:

- Clearly indicate that the previous result no longer corresponds to the current inputs.
- Prevent stale inferred values from being presented as current.
- Invalidate or visually separate the old result.
- Require another Solve action.

Implement appropriate handling for overlapping asynchronous requests.

A slower previous API request must never overwrite the result of a newer request.

---

# 15. RESPONSIVE DESIGN

Implement responsive layouts for desktop, tablet, and mobile.

## Desktop

Two-column workspace:

- Left input sidebar
- Right visualization and results

The visualization receives visual priority.

## Tablet

Adapt column widths or switch to a stacked layout where needed.

Preserve readable input controls.

## Mobile

Use a single-column layout:

1. Header
2. Input panel
3. Target selection
4. Solve action
5. Triangle visualization
6. Results
7. Expandable solution steps

Avoid horizontal scrolling.

Ensure buttons and selectable chips have comfortable touch targets.

SVG must scale without clipping.

Do not rely exclusively on hover interactions; click and keyboard equivalents must exist.

---

# 16. ACCESSIBILITY

Implement basic accessibility requirements:

- Semantic HTML
- Associated labels for all inputs
- Keyboard-accessible controls
- Visible focus indicators
- Adequate color contrast
- Meaningful error messages
- Accessible result status announcements
- Non-color indicators distinguishing known and inferred values
- Accessible descriptions or alternatives for the SVG visualization

Honor reduced-motion preferences.

Avoid unnecessary motion.

---

# 17. BACKEND INTEGRATION

Use the existing FastAPI backend.

Expected endpoints may include:

- POST /api/v1/solve
- GET /api/v1/variables
- GET /api/v1/rules
- GET /api/v1/rules/{id}

Verify the actual implementation before integration.

Create a dedicated API client layer in the frontend.

Requirements:

- Strong TypeScript request and response types.
- Centralized API configuration.
- Consistent error handling.
- Loading and failure states.
- No hard-coded backend URLs throughout components.
- Support a configurable local API base URL.
- Correct CORS or Vite proxy configuration for local development.

Do not silently swallow network or server errors.

If the backend is unavailable, display a clear message with an appropriate recovery action.

---

# 18. TESTING REQUIREMENTS

Testing is mandatory.

Do not consider the task complete after the application merely builds.

## 18.1 Unit Tests

Use Vitest.

Test:

- Input parsing
- Field validation
- Goal selection
- Request construction
- Response formatting
- Display precision
- Stale result behavior
- Triangle geometry coordinate calculations
- Geometry construction eligibility
- Status-to-UI mapping

## 18.2 Component Tests

Use React Testing Library.

Test:

- Input interactions
- Advanced parameter accordion
- Goal selection chips
- Solve button enable/disable behavior
- Loading states
- Results rendering
- Error display
- Inference explanation expansion
- Example selection
- Reset functionality

## 18.3 Integration Tests

Verify that the frontend correctly interacts with the actual FastAPI backend.

Test at least:

- Successful solve
- Insufficient information
- Invalid triangle
- Inconsistent facts
- API failure
- Unknown response or unexpected backend error

Use mock responses for isolated frontend tests, but perform separate real backend integration tests.

## 18.4 End-to-End Tests

Use Playwright to interact with the running application in a real browser.

Test complete user workflows:

**E2E-01: Basic triangle**

Input a = 3, b = 4, c = 5.

Select S, hc, R.

Click Solve.

Verify:
- Correct values.
- SOLVED status.
- Visible triangle.
- Available inference steps.

**E2E-02: SAS**

Input b = 3, c = 4, A = 90°.

Solve for a and S.

Verify:
- a = 5.
- S = 6.
- Correct right-triangle visualization.

**E2E-03: Insufficient information**

Input a = 3.

Request S.

Verify:
- UNRESOLVED state.
- No fabricated geometric solution.

**E2E-04: Invalid triangle**

Input a = 1, b = 2, c = 3.

Verify:
- INVALID state.
- Appropriate user-facing message.

**E2E-05: Inconsistent data**

Input a = 3, b = 4, c = 5, S = 7.

Verify:
- INCONSISTENT state.
- No false success presentation.

**E2E-06: Responsive layout**

Verify desktop, tablet, and mobile layouts.

**E2E-07: Input modification**

Solve a triangle, modify one fact, and verify that previous results become stale or are cleared appropriately.

**E2E-08: Result interaction**

Select a calculated result and verify that the visualization or inference details respond appropriately.

## 18.5 Test Integrity

Do not modify expected outcomes solely to pass tests.

Fix implementation defects at the responsible layer.

Report failed or blocked tests clearly.

Do not claim E2E success without running a real browser.

---

# 19. SCREENSHOT DELIVERY

After implementation, start the actual local application and capture screenshots using Playwright.

Do not use generated mockup images as substitutes for real application screenshots.

Create:

docs/screenshots/

Deliver at least the following screenshots:

1. desktop-initial.png
   - Initial application state.

2. desktop-solved.png
   - Successfully solved 3-4-5 triangle.

3. desktop-inference.png
   - Expanded inference explanation.

4. desktop-invalid.png
   - Invalid triangle state.

5. desktop-unresolved.png
   - Insufficient information state.

6. mobile-solved.png
   - Mobile responsive solved state.

7. tablet-layout.png
   - Tablet responsive layout.

Recommended viewport sizes:

- Desktop: 1440 × 900
- Tablet: 768 × 1024
- Mobile: 390 × 844

Before saving screenshots:

- Ensure the application has loaded.
- Ensure the correct scenario is visible.
- Ensure no developer tools obscure the UI.
- Ensure screenshots show meaningful content.
- Check that text and labels are not clipped.
- Verify that the captured screen reflects the real implementation.

Review all screenshots visually.

If screenshots reveal layout defects, fix the defects and capture the screenshots again.

---

# 20. DOCUMENTATION DELIVERY

Create a dedicated documentation folder.

Suggested structure:

docs/
- screenshots/
- UI_UX_SPECIFICATION.md
- USER_GUIDE.md
- IMPLEMENTATION_SUMMARY.md
- TEST_REPORT.md
- DELIVERY.md

## 20.1 UI_UX_SPECIFICATION.md

Document:

- Final information architecture
- Screen layout
- Components
- Interaction behavior
- Responsive rules
- Visual states
- Mathematical visualization behavior
- Accessibility considerations

Ensure the document reflects the actual implementation, not only the original proposal.

## 20.2 USER_GUIDE.md

Write a practical user guide explaining:

1. How to access the application locally.
2. How to enter known parameters.
3. How to select target parameters.
4. How to solve a triangle.
5. How to interpret results.
6. How to view inference steps.
7. How to interact with the triangle visualization.
8. How to use example problems.
9. How to reset the workspace.
10. How to interpret error and unresolved states.

Include screenshots where useful.

The guide should be understandable to someone unfamiliar with the codebase.

## 20.3 IMPLEMENTATION_SUMMARY.md

Document:

- Final architecture
- Frontend folder structure
- Major React components
- API integration strategy
- Triangle SVG geometry implementation
- State management
- Key technical decisions
- Known limitations
- Future improvements

## 20.4 TEST_REPORT.md

Document:

- Test commands
- Test environment
- Unit test results
- Component test results
- Integration test results
- E2E test results
- Browser and viewport coverage
- Known failures
- Screenshots captured as evidence

Use actual test results.

Do not invent pass counts.

## 20.5 DELIVERY.md

Create a final delivery checklist containing:

- Implemented features
- Required deliverables
- Screenshot paths
- Test status
- Local run instructions
- Known limitations
- Any unfinished tasks

The delivery document should help another developer or instructor quickly verify the application.

---

# 21. README UPDATE

Update the repository's root README.md.

The README must include:

## Project Overview

Explain the purpose of Triangle Solver and the Computational Network approach.

## Features

Summarize:

- Triangle parameter input
- Rule-based inference
- SVG visualization
- Result explanation
- FastAPI integration
- Responsive web interface

## Technology Stack

List frontend and backend technologies.

## Prerequisites

Specify the required Python and Node.js versions.

## Installation

Provide exact instructions for installing backend and frontend dependencies.

## Running Locally

Explain how to start:

1. FastAPI backend.
2. Vite frontend.

Include the exact working directories and terminal commands.

Provide the local URLs for:

- Frontend application
- FastAPI backend
- API documentation

Do not assume commands or ports without verifying the repository configuration.

## Environment Variables

Document all necessary environment variables.

Provide an .env.example when appropriate.

Do not commit secrets.

## Testing

Document how to run:

- Backend tests
- Frontend unit tests
- Component tests
- Playwright E2E tests

## Screenshots

Link to screenshots stored in docs/screenshots/.

## Project Structure

Explain the roles of the main directories.

## Documentation

Link to the documents created in docs/.

## Limitations

Explain relevant mathematical and technical limitations.

Keep the README concise enough for someone to set up and run the application without reading the entire implementation guide.

---

# 22. FINAL ACCEPTANCE CRITERIA

The implementation is complete only when:

- [ ] React + TypeScript + Vite frontend is functional.
- [ ] Tailwind CSS is configured correctly.
- [ ] shadcn/ui components are used appropriately.
- [ ] The interface is visually polished and minimal.
- [ ] All 13 parameters are supported.
- [ ] Basic and advanced inputs are clearly separated.
- [ ] Target selection works.
- [ ] Solve requests reach the actual backend.
- [ ] Calculate All Possible works correctly.
- [ ] Solver statuses are presented correctly.
- [ ] SVG triangle construction is mathematically accurate for supported cases.
- [ ] Visualization handles insufficient and ambiguous geometry safely.
- [ ] Users can interact with geometric annotations.
- [ ] Results are displayed clearly.
- [ ] Inference explanations reflect the actual backend trace.
- [ ] Input changes invalidate stale results.
- [ ] Desktop, tablet, and mobile layouts work.
- [ ] Accessibility requirements are addressed.
- [ ] Unit tests run.
- [ ] Component tests run.
- [ ] Real backend integration is verified.
- [ ] Playwright E2E tests run.
- [ ] Real application screenshots are captured and reviewed.
- [ ] Documentation files are completed.
- [ ] Root README includes accurate local setup instructions.
- [ ] The application can be started locally using the documented procedure.

Do not mark criteria as complete if they have not actually been verified.

---

# 23. EXECUTION INSTRUCTIONS

Proceed with the following workflow:

**Phase 1 — Audit**
- Inspect repository and backend API.
- Identify integration requirements.
- Confirm the project structure.

**Phase 2 — Foundation**
- Set up frontend dependencies.
- Configure Tailwind CSS and shadcn/ui.
- Establish design tokens and base layout.
- Implement typed API communication.

**Phase 3 — Core Interface**
- Implement input panel.
- Implement advanced parameters.
- Implement target selection.
- Implement example presets.
- Implement solve and reset actions.

**Phase 4 — Visualization**
- Implement SVG geometry utilities.
- Implement accurate triangle construction.
- Implement labels and highlighting.
- Handle ambiguous or invalid geometric states.

**Phase 5 — Results and Explanation**
- Implement result summaries.
- Implement inference trace.
- Connect result selection to visualization.
- Implement all solver status presentations.

**Phase 6 — Responsive and Accessibility**
- Refine desktop layout.
- Refine tablet and mobile layouts.
- Improve keyboard accessibility and error messages.

**Phase 7 — Testing and Debugging**
- Run unit tests.
- Run component tests.
- Run integration tests.
- Run Playwright E2E tests.
- Fix defects and rerun affected tests.

**Phase 8 — Visual Verification**
- Start the actual application.
- Capture all required screenshots.
- Visually inspect them.
- Fix layout issues and recapture if necessary.

**Phase 9 — Documentation and Delivery**
- Create the documentation files.
- Update README.md.
- Verify local startup from the documented instructions.
- Prepare the delivery report.

Execute these phases directly in the repository.

Do not ask for confirmation between ordinary implementation steps.

Do not stop after creating component skeletons.

Do not claim screenshots, tests, or functionality exist unless they have actually been produced and verified.

If environmental restrictions prevent browser execution or screenshot capture, document the exact blocker and do not fabricate delivery evidence.

---

# 24. FINAL RESPONSE FORMAT

When implementation is finished, provide a concise delivery report containing:

1. **Implementation Summary**
   - Features completed.
   - Frontend architecture.
   - Backend integration.

2. **Screenshots**
   - Direct links to actual screenshot files.
   - Brief descriptions of what each screenshot demonstrates.

3. **Testing Results**
   - Commands executed.
   - Actual passed/failed counts.
   - Any remaining issues.

4. **How to Run Locally**
   - Exact installation commands.
   - Backend startup command.
   - Frontend startup command.
   - Local application URL.

5. **Documentation**
   - README.md
   - UI_UX_SPECIFICATION.md
   - USER_GUIDE.md
   - IMPLEMENTATION_SUMMARY.md
   - TEST_REPORT.md
   - DELIVERY.md

6. **Known Limitations**
   - Mathematical limitations.
   - Technical limitations.
   - Optional future improvements.

The final result should be a **fully working, visually polished, minimal interactive Triangle Solver**, with a clear inference-based educational experience and verifiable delivery artifacts.

**Begin by auditing the repository, then implement, test, visually verify, document, and deliver the complete application.**