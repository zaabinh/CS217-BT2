# Test Report

Executed on 2026-10-24. All counts below are from actual runs.

## Environment

| Item | Version |
|---|---|
| OS | Windows 11 Home 10.0.26200 |
| Node.js / npm | 24.11.0 / 11.6.1 |
| Python (backend venv) | 3.13 (`Bai1/.venv`) |
| Vite / Vitest | 8.3.5 / 5.0.5 |
| React / TypeScript | 19.3.1 / 7.0.2 |
| Playwright / browser | 1.64.1 / Chromium headless shell 156 |

## Commands and results

All commands run from `Bai1/frontend` unless noted.

| Suite | Command | Result |
|---|---|---|
| Type check + build | `npm run build` | OK (no type errors) |
| Unit (Vitest) | `npx vitest run src/lib/lib.test.ts` | **27 passed**, 0 failed |
| Unit + component | `npm test` | **41 passed**, 0 failed (2 files: 27 unit + 14 component) |
| Integration (real backend) | `npm run test:integration` (uvicorn on :8000) | **9 passed**, 0 failed |
| E2E (Playwright, real browser + real backend) | `npm run test:e2e` | **13 passed**, 0 failed (10 workflow + 3 screenshot) |
| Backend (unchanged) | `..\.venv\Scripts\python.exe -m pytest -q` (from `Bai1`) | **240 passed**, 2 warnings (pre-existing Starlette/HTTPX deprecation) |

## Coverage by requirement

**Unit (`src/lib/lib.test.ts`)**
- Input parsing: empty, invalid and valid input, comma decimals, overflow.
- Contextual validation messages; request facts built from populated fields only, with invalid input refused; precision preserved.
- Display rounding and formula prettifier.
- Status-to-tone mapping and translated messages.
- Dependency-chain trace filter.
- Vertex coordinates: right, obtuse, thin and needle triangles; fit within margins with proportions kept; circumcircle fit.
- 3-4-5 inradius and circumradius; angle arc path; triangle inequality; SSA detection.
- Construction eligibility for every visual state, including stale, UNRESOLVED-with-sides, AAA and SSA.
- API client with stubbed `fetch`: success, network failure, HTTP 422 details, unknown shape, non-JSON body.

**Component (`src/App.test.tsx`)**
- Validation messages, with solving blocked while input is invalid.
- Advanced accordion collapsed by default.
- Chip toggling, Select all and Clear.
- Request construction and results rendering; inputs never overwritten.
- Calculate all sends 13 goals.
- Loading state and duplicate-submission guard.
- A slower older response is ignored.
- Stale banner and invalidated drawing.
- API error with Retry.
- INCONSISTENT shows no success.
- Steps expansion, relevant/full filter and step highlighting.
- Example loading does not solve.
- Reset.

**Integration (`src/lib/api.integration.test.ts`)** — the real FastAPI server with no mocks:
- SOLVED 3-4-5 and SAS.
- Calculate all returns 13 facts.
- UNRESOLVED `a=3`.
- INVALID 1-2-3.
- INCONSISTENT S=7 (message mentions R20).
- SSA is classified as ambiguous.
- HTTP 422 (unknown variable, empty goals) surfaces as `ApiError`.
- An unreachable server gives a network error.

**E2E (`e2e/workflows.spec.ts`)**

| Test | Checks |
|---|---|
| E2E-01 | S = 6, hc = 2.4, R = 2.5, SOLVED, SVG visible, steps include R04 |
| E2E-02 | a = 5, S = 6; drawn side ratios 3:4:5 with b² + c² = a² in SVG pixels |
| E2E-03 | UNRESOLVED, no SVG triangle, placeholder message |
| E2E-04 | INVALID with the plain-language message |
| E2E-05 | INCONSISTENT, no "Solved", no result items, rule shown, no triangle |
| E2E-06 | Two-column layout at 1440×900, stacked at 768×1024 and 390×844, no horizontal overflow, SVG within viewport |
| E2E-07 | Editing a fact shows the stale banner and removes the drawing; re-solve clears it and the value changes |
| E2E-08 | Selecting hc shows the altitude and its steps; R shows the circumcircle; keyboard focus and Enter on a side |

## Browser and viewport coverage

- Chromium only (Playwright `Desktop Chrome` profile).
- Viewports: 1440×900, 768×1024 and 390×844.
- Firefox and WebKit were not run.

## Known failures

None in the final runs. During development, three test-code locator issues were fixed:

- an ambiguous "Reset" button name;
- text matching inside the SVG `<desc>`;
- the integration config merging `include` arrays.

A cold-start E2E run (no servers running) exposed a Windows path-quoting bug in the Playwright `webServer` command. It now uses an absolute, quoted Python path. The final 13/13 E2E run started both servers itself.

Two real UI defects were also fixed after reviewing screenshots:

- angle labels overlapping sides on desktop;
- the solve buttons collapsing in height on mobile.

## Screenshot evidence

`docs/screenshots/` contains 7 images. `e2e/screenshots.spec.ts` captured them from the running app, and each was reviewed visually:

- desktop-initial.png
- desktop-solved.png
- desktop-inference.png
- desktop-invalid.png
- desktop-unresolved.png
- mobile-solved.png
- tablet-layout.png
