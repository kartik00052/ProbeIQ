# ProbeIQ Frontend Design Spec — "The Observatory 3D"

Status: **Locked** (all decisions confirmed with the user on 2026-08-09).
This document is the source of truth for the frontend build. The backend API
contract in `.opencode/technical-spec.md` is authoritative for data shapes.

## 1. Locked decisions

| Dimension | Choice |
|---|---|
| 3D engine | **E2 Hybrid** — CSS 3D + Framer Motion for the console UI; ONE lazy-loaded WebGL scene (react-three-fiber) for the AI presence core |
| Visual direction | **Option 3 — Observatory 3D (restrained)** — the presence is the star, the console stays light |
| App tree | `frontend/src/` is the real app; toolchain lives in `frontend/` (migrated from the nested scaffold) |
| Typography | **T2** — Outfit (UI) + JetBrains Mono (interviewer / transcript) |
| Accent | **C1** — desaturated teal |
| Styling | **S1** — Tailwind v4 + design tokens (console) + plain CSS (WebGL canvas shell) |

## 2. Design principles

1. **Purposeful 3D only.** Every 3D move communicates a state change
   (question arriving, AI thinking, interview complete). No decorative spin,
   no constant particle chaos, no neon, no AI-purple.
2. **Text never rotates.** All typography lives on the `z:0` plane.
   Depth comes from surfaces, not type.
3. **Alive, not frantic.** Springs, never linear timers. Continuous soft
   drift in idle; choreography only on state changes.
4. **Calm by default.** The AI-interview research: low anxiety, no red,
   no urgency signals. The presence is reassuring, never menacing.
5. **Accessibility first.** `prefers-reduced-motion` flattens every 3D
   animation to 2D fades. Zero movement, full experience.

## 3. Anti-patterns (banned)

- Neon gradients, glassmorphism overload, 2026 "AI-uniform" looks
  (indigo/purple gradients, Geist-clone, Vercel-clone)
- Text in 3D, rotating text, scrolljacked layouts
- Constant full-screen particle motion behind the interview
- Faking AI behavior — presence state is **client-derived** from
  request in-flight + done + transcript length only
- Spinner-based loading — use presence states instead

## 4. The presence (WebGL core)

One lazy-loaded react-three-fiber scene. The AI as a luminous GPGPU /
particle-field core. Loaded after first paint; never the LCP element.

State machine (driven by zustand, client-derived):

| State | Trigger | Motion |
|---|---|---|
| `IDLE` | app open, no interview | slow drift, soft breathing |
| `THINKING` | interview request in-flight | core contracts + brightens, spin-up |
| `RESPONDING` | reply arrives | burst, then ease to neutral |
| `WAITING` | awaiting candidate input | calm float |
| `COMPLETE` | `done: true` | collapse into feedback |

Signature moment: on "Begin Interview" the 3D core **collapses into a flat
2D transcript element** (Lusion-style 3D→2D) so focus moves to the interview.

WebGL discipline: dpr-capped, geometry disposal, static poster fallback on
low-tier mobile, scene paused off-screen.

## 5. The console (CSS 3D, Framer Motion)

- Shared `perspective: 1000–1400px` scene; one vanishing point.
- Questions **push in from `z:-100`** with a small `rotateY`, travelling
  through space, not sliding on glass.
- Pointer-tracked depth stack via `useMotionValue → useSpring`:
  bg field `z:0`, floating context cards `z:5`, active question `z:10`.
- Topic transitions: `AnimatePresence mode="wait"`, one consistent 3D
  choreography (old card tilts `rotateX:25` + recedes, new one advances).
- Completion → feedback expands from the collapsed core.

### Spring presets (centralized in `src/lib/motion.ts`)

| Preset | Values | Use |
|---|---|---|
| `snappy` | `{stiffness: 400, damping: 30}` | presence state changes |
| `ui` | `{stiffness: 200, damping: 25}` | cards, questions, parallax |
| `gentle` | `{stiffness: 100, damping: 20}` | breathing, idle drift |

`z`/depth tweens on `circInOut`. Animate `transform` + `opacity` only.
Never `overflow:hidden` or sub-1 opacity on a 3D parent (flattens `preserve-3d`).

## 6. Design tokens

- **Type:** Outfit (UI), JetBrains Mono (interviewer voice, transcript,
  code-adjacent signals). Weights 400/500/600; mono for labels + timestamps.
- **Accent:** desaturated teal (`#5EEAD4`-family but desaturated; exact hex
  pinned in Tailwind theme tokens) — presence glow, highlights, focus.
- **Palette:** deep-space dark base (near-black w/ blue-teal cast),
  glass-light console surfaces, teal glow accents. No white-page mode in
  v1 scope unless decided later.
- **Surfaces:** layered depth — bg field, glass console, elevated question.

## 7. Architecture (per `.opencode/FRONTEND.md` conventions)

- Thin pages, zustand stores, centralized Framer Motion variants in
  `src/lib/motion.ts`, `prefers-reduced-motion` respected, accessible semantics.
- WebGL isolated in `src/components/three/`; zustand drives its state.
- Single backend client against `POST /api/interview` (`.opencode/technical-spec.md`):
  start `{sessionId, candidate}` / turn `{sessionId, message}` →
  `{reply, done, feedback?}`; errors `{error, detail}` 404/409/422/500.
- No fabricated endpoints, responses, or interview states.

## 8. Build plan

1. ✅ Toolchain migrated to `frontend/` (Vite 8, TS, eslint).
2. Scaffold app: pages/components/hooks/api/services/stores/types/constants/
   router/lib/utils + backend client + zustand + motion foundations.
3. Build presence (WebGL core) + console (CSS 3D) per above.
4. Verify: `npm run build` + `npm run lint`.
