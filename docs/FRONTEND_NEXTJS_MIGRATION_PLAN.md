# Frontend React/Vite To Next.js Migration Plan

Generated: 2026-04-28

This plan is tailored to the current `frontend/` app: Vite, React 19, React Router DOM 7, Tailwind CSS 4, Supabase browser auth, and a separate FastAPI backend.

Implementation status on branch `migrate-frontend-nextjs`: the frontend has been converted to Next.js App Router, the old Vite entry files have been removed, React Router has been replaced with `next/navigation`, `/api/*` rewrites to FastAPI, and `npm run build` passes.

Official references checked while preparing this plan:

- Next.js Vite migration guide: https://nextjs.org/docs/pages/guides/migrating/from-vite
- Next.js App Router docs: https://nextjs.org/docs/app
- Next.js ESLint configuration docs: https://nextjs.org/docs/app/api-reference/config/eslint

## Recommendation

Use a two-stage migration on a dedicated branch:

1. First get the current SPA running under Next.js with minimal behavior change.
2. Then migrate React Router routes to App Router files and add server-aware Supabase auth.

This follows the official migration shape and reduces risk because the app is currently heavily client-side: every page uses hooks, state, effects, browser navigation, or browser APIs.

## Goals

- Keep the FastAPI backend unchanged.
- Replace Vite with Next.js in `frontend/`.
- Preserve current routes and page behavior.
- Preserve bearer-token API calls to FastAPI.
- Improve Vercel deployment fit.
- Enable future Server Components, route-level loading states, metadata, and SSR auth.

## Non-Goals For The First Pass

- Do not rewrite backend routes.
- Do not move API business logic into Next.js route handlers.
- Do not convert data-heavy pages to Server Components until auth and API token forwarding are deliberately designed.
- Do not change database schema.

## Baseline Before Migration

Run these before making structural changes:

```bash
cd frontend
npm install
npm run lint
npm run build
```

Also run backend tests:

```bash
cd backend
pytest
```

Record any failures before migration so they are not confused with Next.js regressions.

## Target Dependencies

Add:

- `next`
- `eslint-config-next`
- `@supabase/ssr` if implementing middleware/cookie-aware auth

Keep:

- `react`
- `react-dom`
- `@supabase/supabase-js`
- `lucide-react`

Remove after route migration:

- `vite`
- `@vitejs/plugin-react`
- `@tailwindcss/vite`
- `react-router-dom`
- `eslint-plugin-react-refresh`

## Environment Variable Changes

Next.js only exposes browser variables prefixed with `NEXT_PUBLIC_`.

```text
VITE_SUPABASE_URL       -> NEXT_PUBLIC_SUPABASE_URL
VITE_SUPABASE_ANON_KEY  -> NEXT_PUBLIC_SUPABASE_ANON_KEY
VITE_API_BASE           -> NEXT_PUBLIC_API_BASE
```

Add a server-only API proxy target if using Next rewrites:

```text
API_PROXY_TARGET=http://localhost:8000
```

Production options:

- Direct client API calls: set `NEXT_PUBLIC_API_BASE` to the deployed FastAPI origin.
- Next proxy: keep client calls on `/api` and configure `next.config.ts` rewrites to the deployed FastAPI origin through `API_PROXY_TARGET`.

## Stage 1: Next.js Compatibility Shell

Purpose: boot the existing SPA in Next.js before replacing the router.

1. Create a migration branch.
2. Install Next.js dependencies in `frontend/`.
3. Add `src/app/layout.tsx`.
4. Add `src/app/[[...slug]]/page.tsx` as a client entry that renders the existing `<App />`.
5. Move global CSS import from `main.tsx` to `app/layout.tsx`.
6. Replace `import.meta.env.*` reads with `process.env.NEXT_PUBLIC_*`.
7. Replace Vite scripts with Next scripts:

```json
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "eslint ."
}
```

8. Add `.next` and `next-env.d.ts` to `.gitignore`.
9. Remove `index.html` and `main.tsx` only after the Next entry is working.

At the end of this stage, React Router may still be running inside a single catch-all Next page. This is temporary but useful for validating Supabase auth, API calls, Tailwind, and Vercel build behavior.

## Stage 2: App Router Route Migration

Replace React Router with App Router files.

Target structure:

```text
frontend/src/
- app/
  - layout.tsx
  - login/
    - page.tsx
  - (protected)/
    - layout.tsx
    - page.tsx
    - projects/[id]/page.tsx
    - papers/page.tsx
    - papers/[id]/page.tsx
    - experiments/page.tsx
    - experiments/[id]/page.tsx
    - settings/page.tsx
    - join/[code]/page.tsx
- components/
- context/
- lib/
- types/
- middleware.ts
```

Route mapping:

| Current route | Current component | New App Router file |
| --- | --- | --- |
| `/login` | `pages/Login.tsx` | `app/login/page.tsx` |
| `/` | `pages/Dashboard.tsx` | `app/(protected)/page.tsx` |
| `/projects/:id` | `pages/ProjectDetail.tsx` | `app/(protected)/projects/[id]/page.tsx` |
| `/papers` | `pages/Papers.tsx` | `app/(protected)/papers/page.tsx` |
| `/papers/:id` | `pages/PaperDetail.tsx` | `app/(protected)/papers/[id]/page.tsx` |
| `/experiments` | `pages/Experiments.tsx` | `app/(protected)/experiments/page.tsx` |
| `/experiments/:id` | `pages/ExperimentDetail.tsx` | `app/(protected)/experiments/[id]/page.tsx` |
| `/settings` | `pages/Settings.tsx` | `app/(protected)/settings/page.tsx` |
| `/join/:code` | `pages/JoinProject.tsx` | `app/(protected)/join/[code]/page.tsx` |

Migration substitutions:

```text
useNavigate() from react-router-dom -> useRouter() from next/navigation
navigate("/path")                  -> router.push("/path")
navigate(-1)                       -> router.back()
useParams() from react-router-dom   -> useParams() from next/navigation
NavLink                             -> Link + usePathname()
Navigate                            -> router.replace() or middleware redirect
Outlet                              -> children in layout.tsx
```

Every migrated page should start with:

```tsx
'use client'
```

The existing `Layout` component also needs to be a client component because it uses state, auth context, navigation, and active path state.

## Stage 3: Auth Migration

Minimum viable path:

- Keep `AuthContext` browser-based.
- Mark it `'use client'`.
- Continue using Supabase session tokens to call FastAPI through `api-service.ts`.
- Replace Vite env names with `NEXT_PUBLIC_*`.

Better Next.js path:

- Add `@supabase/ssr`.
- Create browser and server Supabase clients.
- Add `src/middleware.ts` to redirect unauthenticated users away from protected routes.
- Keep `/login` public.
- Protect `/`, `/projects/*`, `/papers/*`, `/experiments/*`, `/settings`, and `/join/*`.

Middleware notes:

- Exclude `/_next/*`, static assets, and `/login`.
- Ensure Supabase OAuth redirect URLs include `http://localhost:3000` and deployed Vercel URLs.
- Keep client-side `AuthProvider` for UI state and sign-in/sign-out methods even when middleware handles initial redirects.

## Stage 4: API And Proxy Setup

Current Vite behavior proxies `/api/*` to FastAPI and strips the `/api` prefix. Match that in `next.config.ts`:

```ts
import type { NextConfig } from 'next'

const apiTarget = process.env.API_PROXY_TARGET ?? 'http://localhost:8000'

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${apiTarget}/:path*`,
      },
    ]
  },
}

export default nextConfig
```

Then set:

```text
NEXT_PUBLIC_API_BASE=/api
API_PROXY_TARGET=http://localhost:8000
```

For production, `API_PROXY_TARGET` should be the deployed FastAPI origin. If not proxying through Next, set `NEXT_PUBLIC_API_BASE` directly to the deployed FastAPI origin and keep backend CORS updated.

Do not break file uploads: `api-service.ts` currently avoids setting `Content-Type` for `FormData`; preserve that behavior.

## Stage 5: Tailwind, Assets, And Metadata

- Use the Next-created `src/app/globals.css` or keep `src/index.css` and import it from `app/layout.tsx`.
- Keep `@import "tailwindcss";`.
- Remove Vite-specific `@tailwindcss/vite` config after Next styling works.
- Replace `frontend/index.html` metadata with `app/layout.tsx` `metadata`.
- Remove unused Vite starter assets (`public/vite.svg`, `src/assets/react.svg`) when confirmed unused.
- Replace the Vite favicon reference with Next metadata or `app/icon.*`.

## Stage 6: Cleanup

Delete Vite/React Router artifacts only after all routes work in App Router:

- `frontend/index.html`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/vite.config.ts`
- `frontend/tsconfig.node.json`
- Vite-only README content
- Vite dependencies
- `frontend/src/components/ProtectedRoute.tsx` if middleware replaces it

Update:

- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/tsconfig.json`
- `frontend/eslint.config.js`
- `frontend/vercel.json` or remove it if Vercel auto-detection is enough

Modern Next.js uses the ESLint CLI directly; do not use `next lint`.

## Verification Checklist

Local:

- `npm run lint`
- `npm run build`
- `npm run dev` serves on `http://localhost:3000`
- Backend runs on `http://localhost:8000`
- `/api/db-ping` or direct backend ping works according to selected proxy strategy

Auth:

- Logged-out visit to `/` redirects to `/login`.
- Email sign-up/sign-in works.
- Google OAuth returns to the Next.js origin.
- Sign out clears UI state and returns to `/login`.

Core flows:

- Dashboard lists projects, papers, and experiments.
- Project create/delete works.
- Project detail loads papers, experiments, members, and invites.
- Invite link generation, copy, revoke, and join work.
- Paper list and paper detail load.
- PDF upload still sends `FormData` and indexes successfully.
- Paper Q&A and project Q&A return answers and citations.
- Experiment create/update/delete works.
- Experiment runs create/update/delete works.
- Notes create/update/delete works in paper and experiment contexts.

Deployment:

- Vercel preview detects Next.js.
- Vercel env vars use `NEXT_PUBLIC_*` names.
- Supabase redirect URLs include the preview and production origins.
- FastAPI `CORS_ORIGINS` includes the Next.js production origin if calls go directly from browser to backend.
- Production API requests do not hit the old SPA fallback.

## Main Risks

- Auth flicker or redirect loops if middleware and client `AuthProvider` disagree.
- API failures if `/api` proxy does not strip the prefix like Vite did.
- Supabase OAuth failures if redirect URLs still point at the old Vite origin.
- Build failures from unconverted `import.meta.env` references.
- Broken active nav styling after `NavLink` is replaced.
- Client/server boundary errors if pages using hooks are not marked `'use client'`.
- Production CORS failures when moving from `localhost:5173` to `localhost:3000` and Vercel origins.

## Cutover Plan

1. Merge only after local build, lint, backend tests, and manual smoke tests pass.
2. Deploy a Vercel preview using the Next.js preset.
3. Add preview URL to Supabase OAuth redirects and backend CORS.
4. Run the verification checklist against preview.
5. Promote preview to production.
6. Keep the previous Vercel deployment available for rollback.

## Suggested Implementation Order

1. Compatibility shell under Next.js.
2. Env variable rename and API proxy.
3. Tailwind/global CSS parity.
4. Auth context compatibility.
5. App Router route files.
6. Middleware auth.
7. Remove React Router and Vite artifacts.
8. Vercel env/deployment cleanup.
