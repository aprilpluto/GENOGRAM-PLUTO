# Pluto Genogram Pintar

**Smart Family Mapping by Pluto for April**

Aplikasi web profesional untuk membuat diagram genogram dari input teks data keluarga. Dibangun dengan Flask, D3.js, dan TailwindCSS — siap deploy ke Vercel.

## Fitur

- Input teks natural & terstruktur (Bahasa Indonesia)
- AI parser untuk analisis hubungan keluarga otomatis
- Simbol genogram standar internasional (laki-laki, perempuan, pernikahan, perceraian, adopsi, kembar, kematian)
- Auto-layout generasi presisi
- Editor interaktif: zoom, drag, undo/redo
- Export: PNG, JPG, SVG, PDF, JSON
- Dark/light mode, template, validasi, rekomendasi perbaikan
- Penyimpanan project lokal (localStorage)

## Struktur Project

```
GENOGRAM/
├── app.py              # Flask entrypoint (Vercel)
├── requirements.txt
├── vercel.json
├── api/
│   └── routes.py       # REST API
├── core/
│   ├── models.py       # Domain models
│   ├── parser.py       # Text parser
│   ├── validator.py    # Validation engine
│   └── layout.py       # Layout engine
├── templates/
│   ├── landing.html
│   └── dashboard.html
└── static/
    ├── css/app.css
    └── js/
        ├── app.js
        ├── genogram-engine.js
        └── export.js
```

## Menjalankan Lokal

```bash
cd GENOGRAM
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Buka http://localhost:5000

## Deploy ke Vercel

1. Install [Vercel CLI](https://vercel.com/docs/cli)
2. Dari folder project:

```bash
vercel
```

3. Atau hubungkan repo GitHub ke Vercel — framework terdeteksi otomatis (Flask/Python).

File `vercel.json` dan `app.py` sudah dikonfigurasi untuk routing Flask + static files.

## Format Input Contoh

```
Ayah: Budi, laki-laki, 55 tahun
Ibu: Sinta, perempuan, 50 tahun
Menikah tahun 1995
Anak 1: Andi, laki-laki, 25 tahun
Anak 2: Rina, perempuan, 20 tahun
Andi menikah dengan Maya, perempuan, 24 tahun
```

## API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/health` | Health check |
| POST | `/api/parse` | Parse teks → graph + layout |
| POST | `/api/validate` | Validasi graph |
| POST | `/api/layout` | Hitung ulang layout |
| GET | `/api/templates` | Daftar template |
| GET | `/api/templates/:id` | Template spesifik |

## Teknologi

- **Backend:** Python 3, Flask
- **Frontend:** HTML, TailwindCSS (CDN), JavaScript
- **Diagram:** D3.js v7
- **Export:** html2canvas, jsPDF

## Branding

**Pluto Genogram Pintar**  
*Smart Family Mapping by Pluto for April*

---

© 2026 Pluto for April
