# Deploy Gratis ke Vercel (Hobby)

Panduan ini mengoptimalkan **Pluto Genogram Pintar** untuk **Vercel Hobby (gratis)**.

## Mengapa konfigurasi ini?

| Masalah umum | Solusi |
|--------------|--------|
| Folder `api/` bentrok dengan Serverless Vercel | Pakai `routes/` (URL API tetap `/api/...`) |
| CSS/JS tidak muncul | Aset di `public/static/` → CDN Vercel |
| Bundle lambat / besar | Hanya `flask` di `requirements.txt` |
| Static diarahkan salah | `vercel.json` → `filesystem` dulu, lalu `app.py` |

## Langkah deploy (gratis)

### 1. Akun Vercel

Buat akun di [vercel.com](https://vercel.com) (Hobby = gratis).

### 2. Push ke GitHub

```bash
git init
git add .
git commit -m "Pluto Genogram Pintar - Vercel ready"
git remote add origin https://github.com/USERNAME/pluto-genogram.git
git push -u origin main
```

### 3. Import di Vercel

1. **Add New Project** → import repo GitHub  
2. Framework: **Other** (atau terdeteksi Flask otomatis)  
3. **Root Directory:** `.`  
4. **Build Command:** kosongkan (tidak perlu build Node)  
5. **Output Directory:** kosongkan  
6. Klik **Deploy**

### 4. Atau via CLI

```bash
npm i -g vercel
cd GENOGRAM
vercel
vercel --prod
```

## Setelah deploy

- Landing: `https://nama-project.vercel.app/`
- Dashboard: `https://nama-project.vercel.app/dashboard`
- Health API: `https://nama-project.vercel.app/api/health`

## Batasan tier gratis (normal)

- **Tidak ada database server** — simpan project di browser (localStorage)
- **Cold start** ~1–3 detik pertama kali buka
- **Timeout function** ~10 detik (cukup untuk parse genogram)
- **Bandwidth** generous untuk aplikasi kecil

## Troubleshooting

### Halaman putih / 500

Cek **Deployments → Logs**. Pastikan `app.py` dan folder `core/` ter-upload.

### CSS/JS 404

Pastikan file ada di `public/static/css/` dan `public/static/js/`.

### `/api/parse` 404

Pastikan tidak ada folder `api/` di root (gunakan `routes/`).

### Build gagal Python

Pastikan `runtime.txt` berisi `python-3.12` dan `requirements.txt` hanya berisi `flask`.

---

**Pluto Genogram Pintar** — *by Pluto for April*
