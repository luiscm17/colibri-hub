# Colibri Hub — Frontend

React application for the Colibri Hub system, built with Mantine UI, Vite, and TypeScript.

## Tech Stack

- **React 19** with TypeScript
- **Mantine 9** component library (core, form, hooks, notifications)
- **Vite 8** build tool
- **React Router 7** for routing
- **React Data Grid** for tabular data
- **Tabler Icons** for iconography

## Quick Start

```bash
cd frontend
pnpm install --frozen-lockfile
pnpm dev
```

The dev server starts at `http://localhost:5173`.

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server with HMR |
| `pnpm build` | Type-check (`tsc -b`) and production build |
| `pnpm lint` | Run ESLint |
| `pnpm preview` | Preview the production build locally |

## Project Structure

```
src/
├── main.tsx          # Entry point (Mantine, notifications, AuthProvider)
├── app/              # Shell layout and routing
└── features/         # Feature modules
```

Path alias `@/*` resolves to `src/*`.

## Documentation

See [frontend/docs/](docs/README.md) for detailed documentation:

- [Architecture Overview](docs/architecture/overview.md)
- [Design System / Visual Identity](docs/design-system/visual-identity.md)
- [Feature Specs](docs/features/bale-management.md)
- [Editable batch grid pattern](docs/patterns/editable-batch-grid.md)

For product requirements and system architecture, see [docs/](../docs/README.md).
