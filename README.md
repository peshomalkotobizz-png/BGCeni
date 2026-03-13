# ЦениBG 🇧🇬

**Проследяване на цени в Lidl, Kaufland, Billa — имейл при намаление**

---

## ⚡ Бързо стартиране (Windows)

1. **Разархивирай** ZIP файла в папка (напр. `C:\cenibg`)
2. **Двойно кликни** `start.bat`
3. Следвай инструкциите в прозореца
4. Приложението се отваря на **http://localhost:5000**

---

## 🔧 Настройка (задължително преди реален старт)

### 1. Stripe (плащания)

1. Регистрирай се на [stripe.com](https://stripe.com)
2. Отиди в **Dashboard → Developers → API keys**
3. Копирай `Publishable key` и `Secret key`
4. Отиди в **Products → Add product**:
   - Название: "ЦениBG Premium"
   - Цена: 4.00 BGN, Recurring Monthly
   - Копирай `Price ID` (изглежда като `price_1ABC...`)
5. Запиши в `.env` файла

### 2. Stripe Webhook (за автоматично деактивиране при отмяна)

```bash
# Инсталирай Stripe CLI: https://stripe.com/docs/stripe-cli
stripe login
stripe listen --forward-to localhost:5000/stripe-webhook
# Копирай whsec_... ключа в .env
```

### 3. Gmail за имейли

1. Включи [2-Step Verification](https://myaccount.google.com/security)
2. Отиди в [App Passwords](https://myaccount.google.com/apppasswords)
3. Генерирай парола за "Mail" → "Windows Computer"
4. Запиши в `.env` файла

---

## 📁 Структура на проекта

```
cenibg/
├── app.py                 # Главен Flask сървър
├── database.py            # База данни (SQLAlchemy модели)
├── requirements.txt       # Python зависимости
├── start.bat              # Windows стартер
├── .env.example           # Шаблон за конфигурация
├── .env                   # Твоята конфигурация (не качвай в Git!)
├── scrapers/
│   └── scraper.py         # Scraping модул (Lidl, Kaufland, Billa)
├── templates/             # HTML шаблони
│   ├── index.html         # Landing page
│   ├── dashboard.html     # Потребителско табло
│   ├── register.html      # Регистрация
│   ├── login.html         # Вход
│   ├── upgrade.html       # Premium страница
│   └── upgrade_success.html
└── cenibg.db              # SQLite база (създава се автоматично)
```

---

## 🤖 Реален Scraping

Файлът `scrapers/scraper.py` съдържа демо данни. За реален scraping:

### Lidl (статичен HTML — лесно)
```python
url = "https://www.lidl.bg/q/search/?q=мляко"
response = requests.get(url, headers=HEADERS)
soup = BeautifulSoup(response.text, "html.parser")
for card in soup.select(".product-grid-box"):
    name = card.select_one(".product-grid-box__description").text.strip()
    price = card.select_one(".m-price__price").text.strip()
```

### Kaufland & Billa (JavaScript — нужен Playwright)
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.kaufland.bg/produkti/mlqko.html")
    page.wait_for_selector(".product-tile", timeout=10000)
    # ... вземи данните
```

**Съвет**: Инспектирай HTML-а с DevTools (F12) → намери CSS класа на цената → запиши го в scraper-а.

---

## 💰 Freemium модел

| | Безплатен | Premium (4 лв./мес.) |
|---|---|---|
| Продукти в Wishlist | До 5 | Неограничени |
| Праг | -10% фиксиран | По избор |
| Проверка | Веднъж дневно | На 6 часа |
| История | 7 дни | 1 година |
| Графики | ❌ | ✅ |

---

## 🌐 Качване в интернет (production)

### Опция 1: Railway.app (препоръчително, безплатно)
```bash
# Инсталирай Railway CLI
npm install -g @railway/cli
railway login
railway init
railway up
```

### Опция 2: Render.com
- Свържи GitHub repo
- Add `gunicorn app:app` като start command
- Добави environment variables

### Опция 3: VPS (DigitalOcean, Hetzner)
```bash
pip install gunicorn
gunicorn app:app --workers 4 --bind 0.0.0.0:5000
```

---

## 📊 API Endpoints

| Метод | URL | Описание |
|---|---|---|
| GET | `/api/products/search?q=мляко&store=Lidl` | Търсене |
| POST | `/api/wishlist/add` | Добави в wishlist |
| POST | `/api/wishlist/remove` | Премахни от wishlist |
| GET | `/api/price-history/{id}` | История на цената |
| POST | `/api/settings` | Запази настройки |
| GET | `/api/scrape-now` | Ръчен scraping |
| POST | `/create-checkout-session` | Stripe checkout |
| POST | `/stripe-webhook` | Stripe events |

---

## 🚀 Вирален потенциал

При 100 платени абоната → **400 лв./мес.** пасивен доход  
При 1000 абоната → **4000 лв./мес.**

**Стратегия за растеж:**
- Сподели в Facebook групи "Икономично домакинство"
- TikTok видео "Спестих 80 лв. за месец с тази Bulgarian app"
- SEO: "lidl акции", "kaufland намаления", "цени хранителни стоки"

---

*Направено с ❤️ за България*
