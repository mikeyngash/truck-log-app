# 🚀 Deployment Guide - Truck Log App

## Prerequisites
- Node.js installed (v18 or higher)
- Python 3.8+ installed
- Git installed

## Step 1: Install CLI Tools

### Install Railway CLI
```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# OR using npm
npm install -g @railway/cli
```

### Install Vercel CLI
```bash
npm install -g vercel
```

### Verify Installation
```bash
railway --version
vercel --version
```

## Step 2: Deploy Backend to Railway

### Navigate to Backend Directory
```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/backend
```

### Login to Railway
```bash
railway login
```
This will open your browser for authentication.

### Initialize and Deploy
```bash
# Initialize Railway project
railway init

# Deploy the backend
railway up
```

### Get Your Backend URL
```bash
railway domain
```

**IMPORTANT:** Copy the URL you get (e.g., `https://truck-log-backend-production.up.railway.app`)

### Set Environment Variables (Optional)
```bash
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS=*.railway.app
```

## Step 3: Update Frontend API URL

### Edit the Frontend Configuration
Open `truck-log-app/frontend/src/App.js` and update line 8:

```javascript
// Change this line:
const API_URL = 'http://localhost:8000';

// To your Railway URL:
const API_URL = 'https://your-railway-url.railway.app';
```

**Replace `your-railway-url` with the actual URL from Railway!**

## Step 4: Deploy Frontend to Vercel

### Navigate to Frontend Directory
```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/frontend
```

### Login to Vercel
```bash
vercel login
```

### Deploy to Production
```bash
vercel --prod
```

Follow the prompts:
- **Set up and deploy?** → Y
- **Which scope?** → Your account
- **Link to existing project?** → N
- **Project name?** → truck-log-app (or your choice)
- **Directory?** → ./ (current directory)
- **Override settings?** → N

### Your Frontend URL
Vercel will give you a URL like: `https://truck-log-app.vercel.app`

## Step 5: Update CORS Settings

After getting your Vercel URL, update the backend CORS settings:

```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/backend
railway variables set CORS_ALLOWED_ORIGINS=https://your-vercel-url.vercel.app
```

## Step 6: Test Your Deployment

1. **Visit your Vercel URL**: `https://your-app.vercel.app`
2. **Test the application**:
   - Enter trip details
   - Generate route
   - Download PDF
   - Verify map displays correctly

## Troubleshooting

### Backend Issues

**View Railway Logs:**
```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/backend
railway logs
```

**Common Issues:**
- **500 Error**: Check Railway logs for Python errors
- **Module not found**: Ensure all dependencies are in requirements.txt
- **Database error**: Railway auto-creates SQLite database

### Frontend Issues

**View Vercel Logs:**
```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/frontend
vercel logs
```

**Common Issues:**
- **Build failed**: Check Node version (use 18.x)
- **API not working**: Verify API_URL in App.js is correct
- **CORS error**: Add Vercel URL to Railway CORS settings

### Redeploy

**Redeploy Backend:**
```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/backend
railway up
```

**Redeploy Frontend:**
```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/frontend
vercel --prod
```

## Quick Command Reference

| Task | Command |
|------|---------|
| Deploy backend | `railway up` |
| View backend logs | `railway logs` |
| Get backend URL | `railway domain` |
| Deploy frontend | `vercel --prod` |
| View frontend logs | `vercel logs` |
| Redeploy backend | `railway up` |
| Redeploy frontend | `vercel --prod` |

## Environment Variables

### Railway (Backend)
- `DEBUG=False` - Disable debug mode in production
- `ALLOWED_HOSTS=*.railway.app` - Allow Railway domains
- `SECRET_KEY=your-secret-key` - Django secret key (optional)

### Vercel (Frontend)
No environment variables needed for this app.

## Post-Deployment Checklist

- [ ] Backend deployed to Railway
- [ ] Frontend deployed to Vercel
- [ ] API_URL updated in frontend
- [ ] CORS configured correctly
- [ ] Test all features work
- [ ] PDF download works
- [ ] Map displays correctly
- [ ] HOS calculations accurate

## Support

If you encounter issues:
1. Check the logs (`railway logs` or `vercel logs`)
2. Verify all URLs are correct
3. Ensure CORS settings include your Vercel domain
4. Check that all dependencies are installed

## Success! 🎉

Your truck log app is now live and accessible worldwide!

- **Backend**: https://your-app.railway.app
- **Frontend**: https://your-app.vercel.app

Ready for your $150 submission!
