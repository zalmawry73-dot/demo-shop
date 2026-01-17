# 🚀 Quick Deploy Cheatsheet

## Step 1: GitHub (2 minutes)
```powershell
cd d:\Store
git init
git add .
git commit -m "Deploy ready"
git branch -M main
```
Create repo: https://github.com/new → name: `demo-shop` → Create

```powershell
git remote add origin https://github.com/YOUR_USERNAME/demo-shop.git
git push -u origin main
```

## Step 2: Render.com (1 minute)
- Go to: https://render.com
- Sign up with GitHub
- Done!

## Step 3: Deploy (2 minutes)
- Dashboard → New + → Blueprint
- Connect `demo-shop` repo
- Apply
- Wait 3-5 mins ⏳

## Step 4: Setup Database (1 minute)
- Open Web Service Shell
- Run: `python setup_production.py`
- Done! ✅

## Step 5: Login (30 seconds)
- Open: https://demo-shop-xxxx.onrender.com/login
- Email: admin@store.com
- Password: admin123
- 🎉 Done!

---

## URLs
- **Dashboard**: `/dashboard`
- **POS**: `/pos`  
- **Products**: `/catalog/products`
- **Orders**: `/orders`
- **Customers**: `/customers`

---

## Update Later
```powershell
git add .
git commit -m "update"
git push
# Auto-deploys! 🚀
```
