# Revision AI — Architecture Decisions

This document records the key decisions made before coding begins (Part 0).

## 1. Deployment Model

**Decision: Split services on Render**

| Service | Runtime | Render Type |
|---|---|---|
| `frontend` | Next.js 14 (App Router) | Web Service |
| `backend` | Python FastAPI | Web Service |

- Both services share the same **MongoDB Atlas** database.
- Frontend calls backend via `NEXT_PUBLIC_BACKEND_URL`.
- Backend allows frontend origin via `FRONTEND_URL` (CORS).

## 2. Authentication

**Decision: Clerk with Gmail OAuth**

- Clerk handles all auth (sign-in, sign-up, session management).
- After first login, user is redirected to an onboarding page to collect name + WhatsApp number.
- Clerk `userId` is stored as `clerkId` in MongoDB `User` collection.
- Frontend sends `clerkId` to backend in request headers for user identification.

## 3. LLM Provider

**Decision: Groq API with Llama 3.3 70B Versatile**

- Default API key is server-side (`GROQ_API_KEY`).
- Users can optionally provide their own Groq API key (stored encrypted in DB).
- Backend checks for user key first, falls back to default.

## 4. WhatsApp Messaging

**Decision: Twilio WhatsApp API**

- **Development**: Use Twilio Sandbox (no approval needed).
- **Production**: Register a WhatsApp Business number (requires Twilio + Meta approval).
- Outbound messages are sent by the scheduler.
- Inbound messages are received via webhook at `/webhook/twilio`.

## 5. Scheduler

**Decision: APScheduler (in-process) + external cron fallback**

- APScheduler runs inside the FastAPI process, checking due schedules every 5 minutes.
- **Risk**: Render free tier spins down after 15 min of inactivity, killing the scheduler.
- **Mitigation options**:
  - Use Render Starter plan ($7/mo) for always-on.
  - Use an external cron service (cron-job.org) to ping `/health` every 10 min to keep alive.
  - Expose a `/api/cron` endpoint that the external cron calls to trigger due schedules.

## 6. AI Framework

**Decision: LangChain for agentic flows**

- **Topic Agent**: Multi-turn clarification with tool use.
- **Revision Agent**: Progressive depth content generation.
- **Doubt Agent**: WhatsApp doubt clarification.

## 7. Database

**Decision: MongoDB Atlas**

- Flexible schema suits varied topic content.
- Accessed via Mongoose (Node.js) and Motor (Python async driver).
- Both runtimes use identical field names and types.

## 8. Env Var Contract

All environment variables are documented in `.env.example` at the project root. Both `frontend/.env.local` and `backend/.env` source from this template.

## Required Accounts & Services

| Service | URL | What You Need |
|---|---|---|
| Clerk | https://clerk.com | Publishable key + Secret key |
| MongoDB Atlas | https://cloud.mongodb.com | Connection string |
| Groq | https://console.groq.com | API key |
| Twilio | https://console.twilio.com | Account SID + Auth Token + WhatsApp Sandbox |
| Render | https://render.com | Account for deployment |
