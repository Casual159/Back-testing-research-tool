# Vercel Deployment Guide (Frontend)

Quick guide for deploying the Next.js frontend to Vercel.

---

## Prerequisites

- ✅ Vercel account: https://vercel.com
- ✅ GitHub repo pushed
- ✅ Backend deployed on Railway

---

## Quick Start

### 1. Connect GitHub to Vercel

1. Go to https://vercel.com/new
2. Click "Import Git Repository"
3. Select your GitHub repo: `Back-testing-research-tool`
4. Click "Import"

### 2. Configure Project

**Framework Preset:** Next.js (auto-detected)

**Root Directory:** `frontend` ⚠️ IMPORTANT!

**Build Command:** `npm run build` (default)

**Output Directory:** `.next` (default)

### 3. Environment Variables

Add in Vercel → Project Settings → Environment Variables:

```env
NEXT_PUBLIC_API_URL=https://respectful-acceptance-testenv.up.railway.app
```

⚠️ Make sure to use your actual Railway backend URL!

### 4. Deploy

Click **"Deploy"** button.

Vercel will:
1. Build the Next.js app
2. Deploy to production
3. Give you a URL like: `https://your-project.vercel.app`

---

## Post-Deployment

### 1. Get Your Frontend URL

After deployment, Vercel shows your URL:
```
https://backtesting-research-tool.vercel.app
```

### 2. Test the Application

Open the URL and verify:
- Homepage loads
- Can navigate to different pages
- API calls work (check browser console for errors)

### 3. Enable CORS on Backend

If you get CORS errors, update your Railway backend to allow the Vercel domain.

In `api/main.py`, add your Vercel URL to allowed origins:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-project.vercel.app",  # Add this
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Automatic Deployments

Vercel automatically deploys when you push to GitHub:

```bash
# Make changes
git add .
git commit -m "update frontend"
git push origin main

# Vercel auto-deploys!
```

### Branch Previews

Every branch gets a preview URL:
- `main` branch → Production: `your-project.vercel.app`
- `feature-x` branch → Preview: `your-project-git-feature-x.vercel.app`

---

## Environment-Specific URLs

### Development (Local)
```bash
cd frontend
npm run dev
# Uses .env.local: http://localhost:8000
```

### Production (Vercel)
```bash
git push origin main
# Uses Vercel env var: https://respectful-acceptance-testenv.up.railway.app
```

---

## Custom Domain (Optional)

### Add Custom Domain

Vercel Dashboard → Project → Settings → Domains

Add your domain:
```
app.yourdomain.com
```

Vercel gives you DNS instructions:
```
CNAME: app.yourdomain.com → cname.vercel-dns.com
```

---

## Common Issues

### API Calls Fail (CORS)

**Error:** `Access-Control-Allow-Origin` in browser console

**Fix:** Add Vercel domain to Railway backend CORS settings (see above)

### Environment Variable Not Working

**Error:** API calls go to `undefined` or wrong URL

**Fix:**
1. Verify `NEXT_PUBLIC_API_URL` is set in Vercel
2. Redeploy: Vercel → Deployments → Latest → "Redeploy"
3. Check that variable starts with `NEXT_PUBLIC_` (required for client-side access)

### Build Fails

**Error:** Build fails in Vercel logs

**Fix:**
1. Check build logs in Vercel dashboard
2. Test build locally: `cd frontend && npm run build`
3. Common issues:
   - TypeScript errors
   - Missing dependencies
   - ESLint errors

### Wrong Directory

**Error:** Vercel tries to build from root instead of `frontend/`

**Fix:**
1. Vercel Dashboard → Project → Settings → General
2. Root Directory: `frontend`
3. Click "Save"
4. Redeploy

---

## Monitoring & Analytics

### View Logs

Vercel Dashboard → Project → Deployments → Select deployment → "View Function Logs"

### Performance Metrics

Vercel Dashboard → Project → Analytics

Shows:
- Page load times
- Unique visitors
- Core Web Vitals

---

## Rollback

### Rollback to Previous Deployment

Vercel Dashboard → Deployments → Select previous → "Promote to Production"

---

## Costs

### Free Tier (Hobby)

- Unlimited deployments
- 100 GB bandwidth/month
- Automatic HTTPS
- Preview deployments
- **Perfect for small projects!**

### Pro Tier ($20/month)

- 1 TB bandwidth
- Team collaboration
- Password protection
- More analytics

---

## Alternative: Deploy to Railway

If you want both frontend and backend on Railway:

### Create railway.toml in frontend/

```toml
[build]
builder = "NIXPACKS"
buildCommand = "npm install && npm run build"

[deploy]
startCommand = "npm start"
```

### Add to Railway

```bash
cd frontend
railway init
railway up
```

### Set Environment Variables

Railway Dashboard → Frontend Service → Variables:
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```

---

## Next Steps

1. ✅ Deploy frontend to Vercel
2. ✅ Test the application
3. ✅ Update backend CORS settings if needed
4. ✅ (Optional) Add custom domain
5. ✅ Setup monitoring

---

## Support

- Vercel Docs: https://vercel.com/docs
- Next.js Docs: https://nextjs.org/docs
- Vercel Discord: https://vercel.com/discord

---

## Quick Reference

```bash
# Deploy via CLI (optional)
npm install -g vercel
cd frontend
vercel

# Production deploy
vercel --prod

# View logs
vercel logs

# List deployments
vercel ls
```
