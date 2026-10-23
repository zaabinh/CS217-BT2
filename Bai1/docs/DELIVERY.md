# Delivery Checklist — Triangle Solver Frontend

## Implemented features

- [x] React 19 + TypeScript + Vite 8 frontend in `frontend/`
- [x] Tailwind CSS v4 (`@tailwindcss/vite`) with design tokens in `src/index.css`
- [x] shadcn/ui-style primitives on Radix: Button, Input, Card, Accordion, Tooltip, Badge, Dialog, Separator
- [x] All 13 parameters: 6 basic inputs, plus 7 in a collapsed "Advanced parameters" section
- [x] Lightweight per-field validation with contextual messages; invalid input is never sent
- [x] Target chips with Select all / Clear; Solve selected; Calculate all possible
- [x] Requests reach the real FastAPI backend through the Vite proxy
- [x] All four statuses presented distinctly; no success shown for INVALID or INCONSISTENT
- [x] Accurate SVG triangle from backend-derived sides (SSS/SAS/ASA/AAS); AAA scale-normalized; SSA flagged as ambiguous
- [x] Hover, focus and click inspection of sides and angles
- [x] Highlighting for altitudes, area, inradius and circumradius
- [x] Result items with Given / Inferred / Unresolved badges; intermediate values listed
- [x] Solution steps from the exact backend trace, with a per-result dependency filter and step highlighting
- [x] Stale-result handling and protection against out-of-order responses
- [x] Example problems, Reset, Help dialog
- [x] Responsive desktop, tablet and mobile layouts; accessibility basics; reduced motion

## Deliverables

| Item | Path |
|---|---|
| Frontend source | `frontend/src/` |
| Tests | `frontend/src/**/*.test.ts(x)`, `frontend/e2e/` |
| Screenshots | `docs/screenshots/*.png` (7 files) |
| UI/UX specification | `docs/UI_UX_SPECIFICATION.md` |
| User guide | `docs/USER_GUIDE.md` |
| Implementation summary | `docs/IMPLEMENTATION_SUMMARY.md` |
| Test report | `docs/TEST_REPORT.md` |
| README (updated) | `README.md` |
| Env example | `frontend/.env.example` |

Screenshot files in `docs/screenshots/`:

- desktop-initial.png
- desktop-solved.png
- desktop-inference.png
- desktop-invalid.png
- desktop-unresolved.png
- mobile-solved.png
- tablet-layout.png

## Test status

Details are in [TEST_REPORT.md](TEST_REPORT.md).

| Suite | Result |
|---|---|
| Unit | 27 passed |
| Component | 14 passed |
| Integration (real backend) | 9 passed |
| E2E (Chromium) | 13 passed |
| Backend | 240 passed |

## Run locally

From `Bai1`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn triangle_knowledge_base.app.api.main:app --host 127.0.0.1 --port 8000
cd frontend; npm install; npm run dev     # second terminal
```

Then open http://127.0.0.1:5173.

## Known limitations

- The drawing appears only after a solve, never as a live preview.
- Only the classic SSA case is labelled ambiguous.
- E2E tests run on Chromium only.
- Backend limitations still apply: no reverse Heron, no SSA branching, and UNRESOLVED does not mean "no solution".

## Unfinished tasks

None of the required items are unfinished. Optional future work is listed in IMPLEMENTATION_SUMMARY.md.
