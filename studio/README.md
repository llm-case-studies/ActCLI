# Studio (SPA) — Scaffold

VSCode-style SPA to configure and visualize seminars via the shared semhost backend.

Structure (proposed)
- src/
  - App (layout shell)
  - pages/ (Models, Seminar, MCP, Locations, Status)
  - components/ (ModelsTable, ParticipantsList, FormatCards, LiveGrid, EventLog)
  - api/ (client wrappers for semhost endpoints)
  - store/ (app/session state)
  - styles/ (theme)

Dev commands (example)
- npm run dev  # Vite dev server; proxy / to http://127.0.0.1:7530
- npm run build
- npm run preview

See docs/Semhost_API_Spec_and_TestPlan.md for API details and test plan.
