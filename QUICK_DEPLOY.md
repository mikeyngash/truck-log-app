# ⚡ Quick Deploy - Copy & Paste Commands

## 🚂 Step 1: Deploy Backend (5 minutes)

```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/backend
railway login
railway init
railway up
railway domain
```

**📝 COPY YOUR RAILWAY URL!** (e.g., `https://truck-log-backend-production.up.railway.app`)

---

## 🎨 Step 2: Update Frontend API URL (1 minute)

Open `truck-log-app/frontend/src/App.js` and change line 8:

```javascript
const API_URL = "https://YOUR-RAILWAY-URL-HERE.railway.app";
```

**Replace with your actual Railway URL!**

---

## 🌐 Step 3: Deploy Frontend (5 minutes)

```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/frontend
npm install -g vercel
vercel login
vercel --prod
```

**📝 COPY YOUR VERCEL URL!** (e.g., `https://truck-log-app.vercel.app`)

---

## ✅ Step 4: Test Your App

Visit your Vercel URL and test:

- ✅ Enter trip details
- ✅ Generate route
- ✅ Download PDF
- ✅ Check map display

---

## 🎉 Done!

Your app is live at:

- **Frontend**: https://your-app.vercel.app
- **Backend**: https://your-app.railway.app

Ready for submission! 🚀

---

## 🔧 If Something Goes Wrong

**View Backend Logs:**

```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/backend
railway logs
```

**View Frontend Logs:**

```bash
cd c:/Users/user/Downloads/TEST/truck-log-app/frontend
vercel logs
```

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
