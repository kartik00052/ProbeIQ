# FRONTEND.md — Frontend engineering rules for ProbeIQ

## Verified stack (as of this document)
- Declared dependencies (`frontend/package.json`): axios, framer-motion,
  react-router-dom, zod, zustand. eslint toolchain under `devDependencies`.
- Source tree structure: `src/` with `pages/`, `components/`, `hooks/`,
  `api/`, `services/`, `stores/`, `types/`, `constants/`, `router/`, `lib/`,
  `utils/`.
- **All files under `frontend/src/` are currently empty (0 bytes).** There is no
  runnable frontend code yet.
- React, TypeScript, and Vite are **not currently verified**: they are not
  declared in `package.json`, and there is no `index.html` or Vite config at the
  `frontend/` root. Do not assume they are configured.

## Scope
If the user requests frontend-only work, do NOT modify backend files.

## Component architecture
- Follow the existing directory conventions:
  - `pages/` — route-level screens.
  - `components/` — reusable UI; group by feature (`candidate/`, `interview/`,
    `feedback/`, `common/`, `ui/`, `animations/`).
  - `hooks/` — reusable logic (e.g. `useInterview`, `useWebSocket`).
  - `api/` — HTTP client and request functions.
  - `services/` — orchestration of api calls and state updates.
  - `stores/` — client state (zustand).
  - `types/` — shared TypeScript types.
- Keep page components thin; put logic in hooks/services/stores.
- Reuse existing components before creating new ones.

## State management
- Use the existing store pattern (zustand store in `src/stores/`).
- Do not add a new state library without justification.

## API integration
- Never invent backend endpoints. Inspect the backend route definitions before
  integrating an API.
- Verify request and response schemas against the backend and
  `.opencode/technical-spec.md`.
- Do not create fake API responses and present them as real backend
  functionality. Clearly label temporary mocks as mocks.
- The backend `POST /api/interview` currently returns a dev placeholder reply;
  do not document it as a working interview API.

## TypeScript rules
- Prefer explicit types for data crossing API boundaries.
- Define shared types in `src/types/`.
- Do not silence type errors to make builds pass without justification.

## Accessibility
- Respect `prefers-reduced-motion`.
- Use semantic HTML and keyboard-accessible interactions.
- Provide accessible labels for form controls.

## Responsive design
- Design for mobile, tablet, and desktop breakpoints.
- Avoid fixed widths that break on smaller viewports.

## Performance
- Avoid unnecessary re-renders and heavy imports.
- Keep motion effects lightweight.

## Error / loading / empty states
- Every async flow should handle loading, error, and empty states
  (`LoadingScreen`, `ErrorMessage` exist as scaffolding).
- Never claim an API works unless actually verified.

## Animation guidelines (Framer Motion)
- Prefer purposeful animation over decorative animation.
- Avoid excessive motion.
- Respect accessibility and reduced-motion preferences.
- Do not introduce visual effects merely because they look impressive.
- Keep consistent motion values; centralize shared variants (e.g.
  `src/lib/motion.ts`, `src/components/animations/variants.ts`).

## UI/UX rules
- Use the UI/UX Pro Max skill when performing UI/UX design tasks.
- Maintain consistent spacing, typography, hierarchy, and interaction patterns.
- Do not redesign unrelated parts of the application without approval.

## Dependency rules
- Check `package.json` before adding a new package; prefer existing tooling.
- Never silently replace a framework/library.
