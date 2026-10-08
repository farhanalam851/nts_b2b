# Not This Season – online store (retail) (Django)

## Run locally
```bash
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # add Razorpay keys
python manage.py makemigrations accounts catalog orders
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo                           # optional demo products + shipping rates
python manage.py runserver
```
Storefront: http://127.0.0.1:8000/ · Staff panel: /dashboard/manage/ · Django admin: /admin/

## Customise for the client
Everything brand/seller specific is in `config/settings.py` (BRAND_*, SELLER_STATE, SELLER_GSTIN, BANK_DETAILS, SHIPPING_GST_RATE).
Colours/fonts: `static/css/style.css`. Logo: replace the text in `templates/base.html`.
Upload real photos in /admin → Products → Product images (copy the look from the Instagram page).

## How it works
- **Customers** sign up with email + phone, add a delivery address and check out. Browsing is public.
- **GST**: prices are GST-inclusive. The GST portion is extracted per product (GST % + HSN) and shown on the invoice as CGST+SGST (delivery state == `SELLER_STATE`) or IGST.
- **Shipping**: *Admin → Shipping rates*: per-state base + per-kg charge, free-above threshold, ETA. Blank state = default.
- **Payments**: Razorpay (UPI/cards/netbanking) with server-side signature verification and webhook; or bank transfer (staff clicks *Mark as paid*).
  Webhook URL: `https://YOURDOMAIN/orders/webhook/razorpay/` (events: payment.captured, order.paid, payment.failed).
- **Reviews**: 1–5 stars, text, optional photo; "Verified purchase" badge if the user bought it; staff can hide reviews in admin.
- **Invoices**: PDF with GST breakup from the order page.

## Go live checklist
`DJANGO_DEBUG=0`, strong `DJANGO_SECRET_KEY`, real `ALLOWED_HOSTS`, PostgreSQL, SMTP email, Razorpay *live* keys,
`python manage.py collectstatic`, serve with `gunicorn config.wsgi` behind nginx (serve /media/ from nginx or S3), HTTPS, backups.
