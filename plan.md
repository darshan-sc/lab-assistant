# Next.js Migration Plan

## Context
The frontend is currently a Vite + React 19 + React Router DOM v7 SPA. The goal is to replace it with Next.js (App Router) to get better Supabase SSR auth, a more natural Vercel deployment story, and the option to add server components later. The FastAPI Python backend is untouched. The migration replaces the `frontend/` directory in-place.

---

## Decisions
- **Router**: App Router (app/ directory)
- **Backend**: Keep FastAPI as-is; Next.js proxies to it
- **Strategy**: Replace `frontend/` in-place (delete Vite project, scaffold Next.js)

---

## Phase 1 — Scaffold Next.js App

Delete `frontend/` and create a fresh Next.js app in its place:

```bash
rm -rf frontend/
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint \
  --app --src-dir --no-turbopack \
  --import-alias "@/*"
```

Install additional deps inside `frontend/`:
```bash
npm install @supabase/supabase-js @supabase/ssr lucide-react
```

---

## Phase 2 — Configuration

### `next.config.ts`
Add rewrites to proxy API calls to FastAPI (port 8000):
```ts
rewrites: async () => [
  { source: '/api/:path*', destination: 'http://localhost:8000/:path*' }
]
```

### Environment Variables
Rename from Vite conventions → Next.js conventions in `.env.local`:
```
# Old (VITE_*)                     → New (NEXT_PUBLIC_*)
VITE_SUPABASE_URL                  → NEXT_PUBLIC_SUPABASE_URL
VITE_SUPABASE_ANON_KEY             → NEXT_PUBLIC_SUPABASE_ANON_KEY
VITE_API_BASE                      → NEXT_PUBLIC_API_BASE
```

Update Vercel dashboard env vars to match.

---

## Phase 3 — Supabase Auth Setup

### `src/lib/supabase.ts` (browser client)
```ts
import { createBrowserClient } from '@supabase/ssr'
export const createClient = () =>
  createBrowserClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
```

### `src/middleware.ts` (route protection)
Uses `createServerClient` from `@supabase/ssr` to read the session from cookies.
- If no session → redirect to `/login`
- Applies to all routes except `/login` and Next.js internals (`/_next/`, `/favicon.ico`)
- Replaces the old `<ProtectedRoute>` component entirely

### `src/context/AuthContext.tsx`
- Keep the same `useAuth()` hook interface: `{ user, session, isAuthenticated, isLoading, signIn*, signOut }`
- Replace `createClient()` from `@supabase/supabase-js` with `createBrowserClient` from `@supabase/ssr`
- Mark as `'use client'`

---

## Phase 4 — Directory Structure

```
frontend/src/
├── app/
│   ├── layout.tsx                  ← root layout (AuthProvider wraps everything)
│   ├── login/
│   │   └── page.tsx                ← public login page
│   └── (protected)/                ← route group (no URL segment)
│       ├── layout.tsx              ← sidebar/nav Layout (auth enforced by middleware)
│       ├── page.tsx                ← Dashboard (/)
│       ├── projects/[id]/
│       │   └── page.tsx
│       ├── papers/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── experiments/
│       │   ├── page.tsx
│       │   └── [id]/page.tsx
│       ├── settings/
│       │   └── page.tsx
│       └── join/[code]/
│           └── page.tsx
├── components/
│   ├── Layout.tsx                  ← migrated as-is
│   └── ui/                         ← migrated as-is (Button, Card, Badge, etc.)
├── context/
│   └── AuthContext.tsx             ← updated imports only
├── lib/
│   ├── supabase.ts                 ← new (browser client factory)
│   └── api-service.ts              ← migrated as-is (update env var refs)
├── types/
│   └── index.ts                    ← migrated as-is
└── middleware.ts                   ← new (auth guard)
```

---

## Phase 5 — Page Migration

All pages are interactive (hooks, modals, forms) → all get `'use client'` at the top.

| Old path | New path | Changes needed |
|----------|----------|----------------|
| `pages/Login.tsx` | `app/login/page.tsx` | `useNavigate` → `useRouter`; `useParams` → `useSearchParams` |
| `pages/Dashboard.tsx` | `app/(protected)/page.tsx` | `useNavigate` → `useRouter` |
| `pages/Projects/ProjectDetail.tsx` | `app/(protected)/projects/[id]/page.tsx` | `useParams` → next/navigation |
| `pages/Papers/Papers.tsx` | `app/(protected)/papers/page.tsx` | `useNavigate` → `useRouter` |
| `pages/Papers/PaperDetail.tsx` | `app/(protected)/papers/[id]/page.tsx` | `useParams` → next/navigation |
| `pages/Experiments/Experiments.tsx` | `app/(protected)/experiments/page.tsx` | `useNavigate` → `useRouter` |
| `pages/Experiments/ExperimentDetail.tsx` | `app/(protected)/experiments/[id]/page.tsx` | `useParams` → next/navigation |
| `pages/Settings.tsx` | `app/(protected)/settings/page.tsx` | No nav changes needed |
| `pages/JoinProject.tsx` | `app/(protected)/join/[code]/page.tsx` | `useParams` → next/navigation |

**React Router → Next.js substitutions (find & replace across all pages):**
```
import { useNavigate } from 'react-router-dom'    → import { useRouter } from 'next/navigation'
import { useParams } from 'react-router-dom'       → import { useParams } from 'next/navigation'
const navigate = useNavigate()                      → const router = useRouter()
navigate('/path')                                   → router.push('/path')
navigate(-1)                                        → router.back()
```

**`ProtectedRoute` component**: Deleted — replaced by `middleware.ts` + `(protected)` route group layout.

---

## Phase 6 — Layout Files

### `app/layout.tsx` (root)
- Sets `<html lang>` and `<body>`
- Wraps children in `<AuthProvider>`
- No sidebar here

### `app/(protected)/layout.tsx`
- Renders the existing `<Layout>` sidebar component around `{children}`
- All protected pages automatically get the sidebar

### `app/login/page.tsx`
- Standalone page, no sidebar
- On successful auth → `router.push('/')`

---

## Phase 7 — Vercel Deployment

- Framework preset: **Next.js** (Vercel auto-detects from `frontend/`)
- Remove any `outputDirectory` / `buildCommand` overrides left from Vite
- Add all `NEXT_PUBLIC_*` env vars in the Vercel dashboard
- FastAPI backend continues to run separately (Docker/Railway/etc.)

---

## Files to Delete
- `frontend/` — entire directory, replaced by scaffolded Next.js app

## Files to Carry Over (copy from old `frontend/src/`)
- `src/components/ui/*`
- `src/components/Layout.tsx`
- `src/types/index.ts`
- `src/lib/api-service.ts` (update `VITE_*` → `NEXT_PUBLIC_*` env var names)
- `src/context/AuthContext.tsx` (update supabase import to `@supabase/ssr`)
- All page components → corresponding `page.tsx` files (update nav hooks + add `'use client'`)

---

## Verification Checklist

- [ ] Login with email → lands on Dashboard
- [ ] Login with Google OAuth → lands on Dashboard
- [ ] Visit `/papers` while logged out → redirects to `/login`
- [ ] No auth flicker on protected pages (middleware handles redirect server-side)
- [ ] Upload a paper / create a project → FastAPI responds via `/api/*` proxy
- [ ] `/papers/:id`, `/projects/:id`, `/experiments/:id` load correct data
- [ ] `/join/:code` joins project and redirects
- [ ] Vercel preview deploy builds successfully with Next.js preset
