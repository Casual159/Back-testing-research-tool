# Auth Architecture

> Implemented 2025-02-22. NextAuth.js v5 + API proxy pattern.

## Overview

User authentication with Google OAuth and email/password, multi-tenant data isolation, and API protection via shared secret.

## Components

### Frontend (Next.js / Vercel)
- **NextAuth.js v5** (beta) with JWT session strategy
- **Providers**: Google OAuth, Credentials (email/password)
- **API Proxy**: `/api/backend/[...path]` catches all client API calls
  - Validates NextAuth session
  - Injects `X-User-Id`, `X-User-Email`, `X-Proxy-Secret` headers
  - Forwards to FastAPI backend
  - Handles SSE streaming (agent chat)

### Backend (FastAPI / Railway)
- **`get_optional_user(request)`** dependency reads `X-User-Id` + validates `X-Proxy-Secret`
  - Returns user dict for authenticated requests
  - Returns `None` for MCP/agent internal calls (backward compatible)
- **`get_current_user(request)`** — strict version, raises 401
- **Auth endpoints**: `/api/auth/sync-user`, `/api/auth/register`, `/api/auth/login`, `/api/auth/me`

### Database
- `users` table: id (UUID), email, name, image_url, password_hash, provider, provider_account_id, email_verified, created_at, updated_at
- `user_id` FK (nullable) on: `projects`, `conversations`, `backtest_reports`
- Migration: `alembic/versions/b2c3d4e5f6a7_add_users_and_multi_tenancy.py`

## Auth Flow

```
Browser → /api/backend/* → NextAuth session check → FastAPI
                              ↓
                    Adds X-User-Id + X-Proxy-Secret headers
                              ↓
                    FastAPI validates X-Proxy-Secret
                    Reads X-User-Id for query filtering
```

### Google OAuth Flow
1. User clicks "Sign in with Google" → NextAuth redirects to Google
2. Google returns token → NextAuth creates JWT session
3. `signIn` callback calls `/api/auth/sync-user` to upsert user in PostgreSQL
4. All subsequent API calls go through proxy with user headers

### Email/Password Flow
1. User registers via `/register` → calls `/api/backend/auth/register` → bcrypt hashes password
2. User logs in → NextAuth Credentials provider calls `/api/auth/login` → validates bcrypt
3. JWT session created, same proxy flow as Google

## Security Model

**Threat**: Unauthorized API usage (Binance data fetching, Claude agent calls = real costs).

**Protection**:
- `PROXY_SECRET` shared between Vercel and Railway
- FastAPI rejects requests without valid `X-Proxy-Secret` header
- Direct access to Railway backend URL is blocked for user-scoped endpoints
- MCP server calls (no auth headers) still work via `get_optional_user` returning None

## Multi-Tenancy

Scoped by `user_id` (each user sees only their data):
- Projects: list, create, get, update, delete
- Reports: list, get, save
- Conversations: list, get, create
- Onboarding preferences

**Not scoped** (shared data): market data (`/api/data/*`), strategies (`/api/strategies/*`)

## Key Files

| File | Purpose |
|------|---------|
| `frontend/lib/auth.ts` | NextAuth config (providers, callbacks) |
| `frontend/app/api/auth/[...nextauth]/route.ts` | NextAuth route handler |
| `frontend/app/api/backend/[...path]/route.ts` | API proxy with auth headers |
| `frontend/lib/contexts/AuthContext.tsx` | React auth context + `useAuth()` hook |
| `frontend/middleware.ts` | NextAuth middleware (route protection) |
| `frontend/app/login/page.tsx` | Login page |
| `frontend/app/register/page.tsx` | Registration page |
| `frontend/components/landing/LandingPage.tsx` | Public landing page |
| `api/dependencies.py` | `get_current_user`, `get_optional_user` |
| `api/main.py` | Auth endpoints + user_id query filtering |

## Environment Variables

### Vercel
| Variable | Purpose |
|----------|---------|
| `AUTH_SECRET` | NextAuth JWT signing key |
| `AUTH_TRUST_HOST` | Must be `true` on Vercel |
| `GOOGLE_CLIENT_ID` | Google OAuth |
| `GOOGLE_CLIENT_SECRET` | Google OAuth |
| `PROXY_SECRET` | Shared secret with backend |

### Railway
| Variable | Purpose |
|----------|---------|
| `PROXY_SECRET` | Must match Vercel's value |

### Local (.env.local)
| Variable | Purpose |
|----------|---------|
| `AUTH_SECRET` | Dev secret |
| `GOOGLE_CLIENT_ID` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | From Google Cloud Console |
| `PROXY_SECRET` | Must match local backend |

## Google Cloud Setup

- Project: "Backtesting Research Tool"
- OAuth 2.0 Client ID (Web application)
- Authorized redirect URIs:
  - `https://back-testing-research-tool.vercel.app/api/auth/callback/google`
  - `http://localhost:3000/api/auth/callback/google`

## Gotchas

- Vercel env vars MUST include **Production** environment (not just Preview/Staging)
- `AUTH_TRUST_HOST=true` required on Vercel for NextAuth v5
- NextAuth v5 is installed as `next-auth@beta` (not `next-auth@5`)
- `middleware.ts` is deprecated in Next.js 16 (warning: use "proxy" instead) — works but will need migration
- All client-side `fetch()` calls must go through `/api/backend/...`, never directly to Railway URL
