# Deploy to Render

## 0. On your computer (once)
1. `python manage.py makemigrations accounts catalog orders` (if not done) – **the `migrations/` folders with `0001_initial.py` must be committed**, Render only runs `migrate`.
2. Test it locally, then push to GitHub (`.env`, `db.sqlite3`, `media/` are git-ignored on purpose):
   ```bash
   git init && git add . && git commit -m "NTS store"
   git branch -M main && git remote add origin https://github.com/<you>/<repo>.git && git push -u origin main
   ```

## 1. Create the services
Render dashboard → **New + → Blueprint** → pick the repo. It reads `render.yaml` and creates the web service + Postgres database.
Fill in the prompted env vars:
| Variable | Value |
|---|---|
| DJANGO_SUPERUSER_EMAIL / PASSWORD | your admin login (created automatically on first build) |
| RAZORPAY_KEY_ID / KEY_SECRET | test keys first, live keys at launch |
| CLOUDINARY_URL | from cloudinary.com → Dashboard (`cloudinary://key:secret@cloud`) – needed so product photos survive redeploys |

## 2. Photos
Render's disk is wiped on each deploy. Either:
- **Cloudinary (recommended, has a free tier)**: set `CLOUDINARY_URL`. Photos uploaded in /admin go to Cloudinary automatically.
- **Render Disk (paid web service)**: add a disk mounted at `/var/data` and set `MEDIA_ROOT=/var/data/media`.

## 3. Razorpay
Dashboard → Webhooks → URL `https://<your-service>.onrender.com/orders/webhook/razorpay/`, events `payment.captured`, `order.paid`, `payment.failed`; put its secret in `RAZORPAY_WEBHOOK_SECRET` and redeploy.

## 4. Custom domain
Service → Settings → Custom Domains → add `www.yourdomain.com`, create the DNS record Render shows, then add the domain to env vars:
`DJANGO_ALLOWED_HOSTS=www.yourdomain.com,yourdomain.com` and `CSRF_TRUSTED_ORIGINS=https://www.yourdomain.com,https://yourdomain.com`.

## 5. After first deploy
- Log in at `/admin/` with the superuser; add categories, drops, products + photos, shipping rates.
- Edit seller GSTIN, address, bank details in `config/settings.py` and push.
- To load demo data once: add env `SEED_DEMO=1`, redeploy, then delete the variable.

## Notes
- **Free plan**: the web service sleeps after idle time (first visit is slow) and free databases have limits/expiry – use paid plans for a real store.
- **Email**: Render may block outbound SMTP on free instances; use a paid instance or an email provider with an HTTPS API if order emails don't arrive.
- Updates: `git push` → Render redeploys and runs `migrate` automatically.
