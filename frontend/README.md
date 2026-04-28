# ResearchNexus Frontend

This frontend is a Next.js App Router application that talks to the FastAPI backend through `/api/*` rewrites.

## Development

```bash
npm install
npm run dev
```

The app runs at `http://localhost:3000`. The backend should be available at `http://localhost:8000` unless `API_PROXY_TARGET` is set.

## Environment

Use Next.js public env names:

```env
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_BASE=/api
API_PROXY_TARGET=http://localhost:8000
```

`NEXT_PUBLIC_API_BASE` defaults to `/api`, and `next.config.ts` rewrites `/api/:path*` to the FastAPI backend with the `/api` prefix stripped.

## Scripts

```bash
npm run dev
npm run build
npm run lint
npm run start
```
