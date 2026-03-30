# Revision AI — Deployment Guide

## Quick Deploy on Render

### Option 1: Render Blueprint (Recommended)
1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect your GitHub repo — it will auto-detect `render.yaml`
4. Fill in the secret env vars when prompted

### Option 2: Manual Deploy

#### Backend (FastAPI)
1. **New Web Service** → connect your repo
2. **Root Directory**: `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`

#### Frontend (Next.js)
1. **New Web Service** → connect your repo
2. **Root Directory**: `frontend`
3. **Build Command**: `npm install && npx prisma generate && npm run build`
4. **Start Command**: `npm start`
5. Add environment variables from `.env.example`
6. Set `NEXT_PUBLIC_BACKEND_URL` to your backend's Render URL

## Required Environment Variables

### Frontend (`.env.local`)
```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
DATABASE_URL=mongodb+srv://...
NEXT_PUBLIC_BACKEND_URL=https://your-backend.onrender.com
```

### Backend (`.env`)
```
MONGODB_URI=mongodb+srv://...
GROQ_API_KEY=gsk_...
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
FRONTEND_URL=https://your-frontend.onrender.com
```

## Local Development
```bash
# Frontend
cd frontend
cp ../.env.example .env.local  # fill in values
npm install && npx prisma generate && npm run dev

# Backend (separate terminal)
cd backend
cp ../.env.example .env  # fill in values
python -m venv venv && venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Important Notes
- **Free Tier**: Server spins down after 15 min of inactivity. First request takes ~30s to wake.
- **Scheduler**: Won't work reliably on free tier—use [cron-job.org](https://cron-job.org) to ping `/health` every 14 min.
- **Twilio Sandbox**: Works for development. Production needs WhatsApp Business API approval.
