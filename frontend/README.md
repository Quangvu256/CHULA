# Frontend (Angular)

One folder per screen, singletons in `core/`:

```
src/app/
├── app.ts               shell: the five tabs
├── app.config.ts        providers (HttpClient)
├── core/
│   ├── api.ts           REST client for the Python backend
│   └── state.ts         cross-tab state (last audit result, tab, pending focus)
└── pages/
    ├── check/           IFC upload + verdict + per-check results
    ├── requirements/    the 13 requirements as a folder tree with cited clauses
    ├── graph/           canvas knowledge-graph explorer (deterministic layout, fullscreen)
    ├── method/          extraction pipeline + live accuracy formulas (EN/VI in i18n.ts)
    └── policies/        privacy, copyright, governance defaults
```

Dev: `npx ng serve --proxy-config proxy.conf.json` (backend on :8000).
Build: `npx ng build` - the Python backend serves `dist/frontend/browser`.
Global styles in `src/styles.css` are the ported design system; keep visual
changes there so all pages stay consistent.
