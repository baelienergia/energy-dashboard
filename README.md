# Energy Dashboard — Auto-Update

Repository GitHub che aggiorna automaticamente la **Baeli Energia Energy Dashboard** ogni giorno tramite GitHub Actions e la pubblica su GitHub Pages.

## 🎯 Cosa fa

Ogni mattina alle **08:30 ora italiana**, GitHub Actions:

1. Scarica EUR/USD da Frankfurter API (gratis, no key)
2. Scarica Brent e TTF da Yahoo Finance
3. Aggiorna il file `cache/history.json` con i nuovi valori
4. Genera `public/index.html` dal template
5. Pubblica su GitHub Pages → URL pubblico stabile

## 📁 Struttura

```
dashboard_auto/
├── .github/workflows/update.yml   ← Schedule cron (06:30 UTC)
├── scripts/
│   └── update_dashboard.py        ← Script che fa tutto
├── template/
│   └── template.html              ← Template HTML (NON modificare)
├── public/
│   └── index.html                 ← Generato (deploy su Pages)
├── cache/
│   └── history.json               ← Storico mensile persistente
└── README.md
```

## 🚀 Setup iniziale (una volta sola)

### 1. Crea il repo su GitHub

```bash
# Sul tuo PC
mkdir energy-dashboard && cd energy-dashboard
# Copia tutti i file di questo pacchetto qui
git init
git add .
git commit -m "Initial commit"

# Crea repo su github.com (privato o pubblico, indifferente)
git remote add origin https://github.com/TUOUTENTE/energy-dashboard.git
git branch -M main
git push -u origin main
```

### 2. Attiva GitHub Pages

Sul repo GitHub:
- **Settings** → **Pages**
- Source: **GitHub Actions**

### 3. Attiva i permessi delle Actions

- **Settings** → **Actions** → **General**
- Workflow permissions: **Read and write permissions**
- ✅ Allow GitHub Actions to create and approve pull requests

### 4. Esegui il primo run manuale

- Tab **Actions** in alto
- Workflow **Update Energy Dashboard**
- Bottone **Run workflow** → **Run workflow**

Dopo ~1 minuto avrai:
- Il file `public/index.html` generato e committato
- La pagina pubblicata su `https://TUOUTENTE.github.io/energy-dashboard/`

## 🌐 Collegare il sottodominio `dashboard.baeli.it`

Una volta che GitHub Pages funziona:

1. **Settings** → **Pages** → **Custom domain** → inserisci `dashboard.baeli.it` → Save
2. GitHub creerà automaticamente un file `CNAME` nel repo
3. Sul pannello DNS di OVH (`baeli.it`), aggiungi un record:
   ```
   Tipo:  CNAME
   Nome:  dashboard
   Target: TUOUTENTE.github.io.
   ```
4. Attendi ~10 minuti la propagazione DNS
5. ✅ Spunta **Enforce HTTPS** su GitHub (dopo che il certificato è emesso)

Il link pubblico stabile sarà: **https://dashboard.baeli.it**

## ⏰ Modificare l'orario di aggiornamento

Apri `.github/workflows/update.yml` e modifica la riga `cron`:

```yaml
schedule:
  - cron: '30 6 * * *'   # 06:30 UTC = 08:30 ora italiana (estate)
```

Esempi utili:
- `0 5 * * *` → 07:00 italia
- `0 11 * * *` → 13:00 italia (PUN del giorno è già pubblicato)
- `0 6,18 * * *` → due volte al giorno
- `30 6 * * 1-5` → solo lunedì-venerdì

## 🔧 Aggiornamento manuale dei dati storici

Se ARERA pubblica un nuovo PUN mensile o vuoi correggere uno storico, edita `cache/history.json` su GitHub (anche dal browser, tasto matita) e committa. Al prossimo run il file rispetterà le modifiche.

## 🧪 Test in locale (opzionale)

```bash
pip install requests beautifulsoup4 yfinance lxml
python scripts/update_dashboard.py
# Apri public/index.html nel browser per controllare
```

## 💰 Costi

**Zero.**
- GitHub Actions: 2.000 minuti/mese gratis su repo pubblici, illimitati su privati Free
- GitHub Pages: gratis, banda illimitata
- Frankfurter API: gratis, no key
- Yahoo Finance: gratis (yfinance scraping)

## 🆘 Troubleshooting

**Il workflow fallisce con "permission denied"**
→ Settings → Actions → General → Workflow permissions: **Read and write**

**GitHub Pages non si aggiorna**
→ Controlla tab Actions: il job **Deploy su GitHub Pages** dev'essere ✅ verde

**Dati live non si aggiornano**
→ Controlla i log del workflow nel tab Actions. yfinance/Frankfurter possono fallire occasionalmente — lo script continua comunque con i valori precedenti.

**Voglio cambiare il template grafico**
→ Modifica solo `template/template.html`. Lascia inalterati i due placeholder `__DATA_PLACEHOLDER__` e `__DATE_PLACEHOLDER__`.

---

**Baeli Energia** — COGITHO SAS · P.IVA 05562760875
