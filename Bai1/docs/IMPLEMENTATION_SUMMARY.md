# Implementation Summary — Frontend

## Architecture

```
Browser (React SPA) ──fetch /api/v1/solve──▶ Vite dev proxy ──▶ FastAPI (unchanged)
                                                              └─ SolverService → InferenceEngine → Validator
```

- The backend was **not modified**. All 240 backend tests still pass.
- The frontend does no inference. It sends facts and goals, then renders the response, including the exact trace.

## Folder structure

```
frontend/
├─ index.html, vite.config.ts, vitest.integration.config.ts, playwright.config.ts, .env.example
├─ src/
│  ├─ main.tsx, App.tsx, index.css
│  ├─ components/
│  │  ├─ InputPanel.tsx, TriangleView.tsx, ResultsPanel.tsx, Sym.tsx
│  │  └─ ui/  button, input, card, badge, accordion, tooltip, dialog, separator
│  ├─ lib/
│  │  ├─ api.ts          typed client, ApiError, response shape check
│  │  ├─ variables.ts    13 variables, names, groups Q01–Q10
│  │  ├─ input.ts        parsing / lightweight validation / request facts
│  │  ├─ format.ts       display rounding, formula prettifier
│  │  ├─ status.ts       status → tone, backend message → plain language
│  │  ├─ trace.ts        dependency-chain filter over the trace
│  │  ├─ geometry.ts     visual state, vertex layout, circles, arcs
│  │  ├─ examples.ts
│  │  ├─ lib.test.ts                 unit tests
│  │  └─ api.integration.test.ts     real-backend tests
│  ├─ App.test.tsx       component tests (React Testing Library)
│  └─ test/setup.ts
└─ e2e/  workflows.spec.ts (E2E-01…08), screenshots.spec.ts, helpers.ts
```

## Major components

| Component | Responsibility |
|---|---|
| `App` | Owns all state with React hooks and runs requests. `solve` is injectable, so tests can mock it. |
| `InputPanel` | Stateless form: fields, advanced accordion, example select, target chips, actions |
| `TriangleView` | Picks the placeholder or constructed SVG. Keeps local UI state for hover, labels and expand. |
| `ResultsPanel` | Status box, stale banner, result items, intermediate values, solution steps with relevant/full view |

## API integration

- `lib/api.ts` defines TypeScript mirrors of `SolveRequest`, `InferenceStep` and `SolveResponse` from `models/`.
- The base URL comes from `VITE_API_BASE_URL`. When it is empty, requests go same-origin and the Vite proxy forwards `/api` to `VITE_BACKEND_URL` (default `http://127.0.0.1:8000`). No CORS change was needed.
- Errors are typed `ApiError` with a kind:

  | Kind | Cause |
  |---|---|
  | `network` | Server unreachable |
  | `http` | Non-2xx status, e.g. 422 with Pydantic messages |
  | `format` | Non-JSON body or unknown shape |

  Each is shown in an alert with a Retry button.
- **Calculate all possible** sends all 13 variables as `goals`. `InferenceEngine.solve` stops only when every goal is known or a pass adds nothing, so this returns the full closure. It reuses the existing contract.

## SVG geometry

`lib/geometry.ts`:

- `visualState(response, stale)` maps the response to placeholder, constructed, ambiguous, invalid or inconsistent. It works independently of the solver status.
- `rawVertices` places B = (0, 0) and C = (a, 0), then finds A from the side lengths.
- `fitLayout` scales uniformly into the box, centers and flips y. It can include the circumcircle in the bounds.
- `incircle`, `circumcircle`, `foot`, `angleArc` and `pushAway` position overlays and labels.

Only the sides returned by the backend are drawn. AAA uses sin A : sin B : sin C, marked as scale-normalized. SSA is recognized and not drawn.

## State management

`useState` in `App` holds:

- raw inputs, targets, advanced/steps accordion state;
- loading, result (`{response, given, goals, mode}`), stale flag, error;
- selected result, selected step, step view.

Derived values (parsed fields, highlight, visual state) are computed during render.

Request ordering:
- `requestId` (a ref) is incremented per request.
- The previous `AbortController` is aborted.
- A response is applied only if its id is still current.

No global store is used.

## Key decisions

- Text inputs with `inputMode="decimal"` rather than `type="number"`, so empty and invalid stay distinguishable.
- Client validation covers only the per-field domain (positive lengths, 0 < angle < 180). Triangle inequality and consistency are left to the backend, whose message is translated to plain language and also shown verbatim.
- Group names Q01–Q10 come from `IMPLEMENTATION_GUIDE.md`. They are display labels only.
- shadcn/ui components were written by hand in shadcn style instead of using the CLI. They behave the same, with no generator step.

## Known limitations

- The visualization appears only after a solve. It is not a live preview while typing, by design: it never shows geometry the backend has not confirmed.
- Two sides plus area also has two possible shapes, but it is shown as "insufficient" rather than "ambiguous". Only classic SSA is detected.
- The browser-side API client validates the response shape only at the top level.
- Only Chromium was tested end to end.
- The UI is English, while the backend docs and messages are partly Vietnamese. The verbatim solver message is shown in its original language.

## Future improvements

- Show both SSA configurations once the backend supports branching.
- Add a rule browser using `GET /api/v1/rules`.
- Export the solution steps.
- Add Firefox and WebKit to the E2E matrix.
