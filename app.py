"""
ЦениBG - Главен Flask сървър
Стартира уеб приложението, API и планировщика за scraping
"""

import os
import json
import threading
import schedule
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_mail import Mail, Message
import stripe
from database import db, User, Product, PriceHistory, Wishlist
from scrapers.scraper import run_all_scrapers

# ── Инициализация ──────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cenibg-dev-secret-change-in-prod")

# База данни (SQLite по подразбиране, лесно се сменя с PostgreSQL)
db_url = os.getenv("DATABASE_URL", "sqlite:///cenibg.db")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_REPLACE_ME")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_REPLACE_ME")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID", "price_REPLACE_ME")  # 4 лв./мес.
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_REPLACE_ME")

# Имейл
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME", "")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD", "")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_USERNAME", "alert@cenibg.com")
mail = Mail(app)


# ── Помощни функции ────────────────────────────────────────
def send_price_alert(user_email, dropped_items):
    """Изпраща имейл при падане на цена."""
    if not dropped_items:
        return
    try:
        items_html = ""
        for item in dropped_items:
            pct = round((1 - item["new_price"] / item["old_price"]) * 100)
            items_html += f"""
            <tr>
              <td style="padding:12px;border-bottom:1px solid #2a2a3d">
                {item['emoji']} {item['name']}<br>
                <small style="color:#6b6b8a">{item['store']}</small>
              </td>
              <td style="padding:12px;border-bottom:1px solid #2a2a3d;text-decoration:line-through;color:#6b6b8a">
                {item['old_price']:.2f} лв.
              </td>
              <td style="padding:12px;border-bottom:1px solid #2a2a3d;color:#4cff6e;font-weight:700">
                {item['new_price']:.2f} лв.
              </td>
              <td style="padding:12px;border-bottom:1px solid #2a2a3d;color:#e8ff00;font-weight:700">
                -{pct}%
              </td>
            </tr>"""

        html_body = f"""
        <div style="background:#0a0a0f;font-family:Inter,sans-serif;padding:40px;max-width:600px;margin:0 auto">
          <div style="font-family:Unbounded,sans-serif;font-size:24px;font-weight:900;color:#e8ff00;margin-bottom:8px">ЦениBG</div>
          <p style="color:#6b6b8a;margin-bottom:24px">Известие за намаление на цена</p>

          <h2 style="color:#f0f0f8;margin-bottom:16px">🔔 {len(dropped_items)} продукт(а) поевтиня!</h2>

          <table style="width:100%;border-collapse:collapse;background:#1a1a26;border-radius:12px;overflow:hidden">
            <thead>
              <tr style="background:#12121a">
                <th style="padding:12px;text-align:left;color:#6b6b8a;font-size:12px">ПРОДУКТ</th>
                <th style="padding:12px;text-align:left;color:#6b6b8a;font-size:12px">БЕШЕ</th>
                <th style="padding:12px;text-align:left;color:#6b6b8a;font-size:12px">СЕГА</th>
                <th style="padding:12px;text-align:left;color:#6b6b8a;font-size:12px">СПЕСТЯВАШ</th>
              </tr>
            </thead>
            <tbody>{items_html}</tbody>
          </table>

          <div style="margin-top:24px;text-align:center">
            <a href="http://localhost:5000/dashboard" 
               style="background:#e8ff00;color:#000;padding:14px 32px;border-radius:8px;font-weight:700;text-decoration:none;display:inline-block">
              Виж всички оферти →
            </a>
          </div>

          <p style="color:#6b6b8a;font-size:12px;margin-top:24px;text-align:center">
            Получаваш този имейл защото следиш продукти в ЦениBG.<br>
            <a href="http://localhost:5000/unsubscribe" style="color:#e8ff00">Спри нотификациите</a>
          </p>
        </div>"""

        msg = Message(
            subject=f"🔔 {len(dropped_items)} продукт(а) поевтиня — ЦениBG",
            recipients=[user_email],
            html=html_body
        )
        mail.send(msg)
        print(f"[EMAIL] Изпратен до {user_email} за {len(dropped_items)} продукта")
    except Exception as e:
        print(f"[EMAIL ERROR] {e}")


def check_price_alerts():
    """Проверява всички wishlist-и и изпраща имейли при намаления."""
    with app.app_context():
        print(f"[{datetime.now()}] Проверка за намаления...")
        users = User.query.all()
        for user in users:
            dropped = []
            for wl in user.wishlists:
                product = wl.product
                history = PriceHistory.query.filter_by(product_id=product.id)\
                    .order_by(PriceHistory.date.desc()).limit(2).all()
                if len(history) >= 2:
                    new_p = history[0].price
                    old_p = history[1].price
                    pct_drop = (1 - new_p / old_p) * 100 if old_p > 0 else 0
                    threshold = user.alert_threshold or 10
                    if pct_drop >= threshold:
                        dropped.append({
                            "name": product.name,
                            "emoji": product.emoji,
                            "store": product.store,
                            "old_price": old_p,
                            "new_price": new_p,
                        })
            if dropped:
                send_price_alert(user.email, dropped)


def run_scheduler():
    """Фонов thread за планиране на scraping и проверки."""
    schedule.every(6).hours.do(lambda: run_all_scrapers(app))
    schedule.every(6).hours.do(check_price_alerts)
    while True:
        schedule.run_pending()
        time.sleep(60)


# ── Маршрути: Публични страници ────────────────────────────
@app.route("/")
def index():
    products_count = Product.query.count()
    users_count = User.query.count()
    return render_template("index.html",
                           products_count=products_count,
                           users_count=users_count,
                           stripe_pub_key=STRIPE_PUBLISHABLE_KEY)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        data = request.get_json() or request.form
        email = data.get("email", "").strip().lower()
        name = data.get("name", "").strip()

        if not email or "@" not in email:
            return jsonify({"error": "Невалиден имейл"}), 400

        existing = User.query.filter_by(email=email).first()
        if existing:
            return jsonify({"error": "Имейлът вече е регистриран"}), 400

        user = User(email=email, name=name, plan="free", alert_threshold=10)
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        return jsonify({"success": True, "redirect": "/dashboard"})

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json() or request.form
        email = data.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            session["user_id"] = user.id
            return jsonify({"success": True, "redirect": "/dashboard"})
        return jsonify({"error": "Имейлът не е намерен"}), 404
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ── Маршрути: Dashboard ────────────────────────────────────
@app.route("/dashboard")
def dashboard():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    user = User.query.get(user_id)
    if not user:
        return redirect("/login")

    wishlist_products = []
    for wl in user.wishlists:
        p = wl.product
        history = PriceHistory.query.filter_by(product_id=p.id)\
            .order_by(PriceHistory.date.desc()).limit(2).all()
        current_price = history[0].price if history else p.current_price
        prev_price = history[1].price if len(history) >= 2 else current_price
        wishlist_products.append({
            "id": p.id,
            "name": p.name,
            "emoji": p.emoji,
            "store": p.store,
            "current_price": current_price,
            "prev_price": prev_price,
        })

    return render_template("dashboard.html", user=user, wishlist=wishlist_products,
                           stripe_pub_key=STRIPE_PUBLISHABLE_KEY)


# ── API ────────────────────────────────────────────────────
@app.route("/api/products/search")
def search_products():
    q = request.args.get("q", "").strip()
    store_filter = request.args.get("store", "all")

    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if store_filter != "all":
        query = query.filter(Product.store == store_filter)

    products = query.limit(30).all()
    user_id = session.get("user_id")
    wishlist_ids = set()
    if user_id:
        wishlist_ids = {wl.product_id for wl in Wishlist.query.filter_by(user_id=user_id).all()}

    result = []
    for p in products:
        history = PriceHistory.query.filter_by(product_id=p.id)\
            .order_by(PriceHistory.date.desc()).limit(2).all()
        current = history[0].price if history else p.current_price
        prev = history[1].price if len(history) >= 2 else current
        result.append({
            "id": p.id,
            "name": p.name,
            "emoji": p.emoji,
            "store": p.store,
            "current_price": current,
            "prev_price": prev,
            "in_wishlist": p.id in wishlist_ids,
        })
    return jsonify(result)


@app.route("/api/wishlist/add", methods=["POST"])
def add_to_wishlist():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Влез в профила си"}), 401

    user = User.query.get(user_id)
    data = request.get_json()
    product_id = data.get("product_id")

    # Лимит за безплатен план
    if user.plan == "free":
        count = Wishlist.query.filter_by(user_id=user_id).count()
        if count >= 5:
            return jsonify({
                "error": "Безплатният план позволява до 5 продукта. Обнови до Premium.",
                "upgrade": True
            }), 403

    existing = Wishlist.query.filter_by(user_id=user_id, product_id=product_id).first()
    if not existing:
        wl = Wishlist(user_id=user_id, product_id=product_id)
        db.session.add(wl)
        db.session.commit()

    return jsonify({"success": True})


@app.route("/api/wishlist/remove", methods=["POST"])
def remove_from_wishlist():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Влез в профила си"}), 401
    data = request.get_json()
    Wishlist.query.filter_by(user_id=user_id, product_id=data.get("product_id")).delete()
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/price-history/<int:product_id>")
def price_history(product_id):
    history = PriceHistory.query.filter_by(product_id=product_id)\
        .order_by(PriceHistory.date.asc()).all()
    return jsonify([{"date": h.date.strftime("%Y-%m-%d"), "price": h.price} for h in history])


@app.route("/api/settings", methods=["POST"])
def update_settings():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Не е влязъл"}), 401
    data = request.get_json()
    user = User.query.get(user_id)
    user.alert_threshold = int(data.get("threshold", 10))
    db.session.commit()
    return jsonify({"success": True})


@app.route("/api/scrape-now")
def scrape_now():
    """Ръчно стартиране на scraper (само за тест)."""
    thread = threading.Thread(target=lambda: run_all_scrapers(app))
    thread.daemon = True
    thread.start()
    return jsonify({"message": "Scraping стартиран в background"})


# ── Stripe плащания ────────────────────────────────────────
@app.route("/upgrade")
def upgrade():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    return render_template("upgrade.html", stripe_pub_key=STRIPE_PUBLISHABLE_KEY)


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Влез в профила си"}), 401
    user = User.query.get(user_id)

    try:
        checkout = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user.email,
            line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
            success_url=request.host_url + "upgrade/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.host_url + "upgrade",
            metadata={"user_id": str(user_id)},
        )
        return jsonify({"url": checkout.url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upgrade/success")
def upgrade_success():
    session_id = request.args.get("session_id")
    if session_id:
        try:
            checkout = stripe.checkout.Session.retrieve(session_id)
            user_id = int(checkout.metadata.get("user_id", 0))
            user = User.query.get(user_id)
            if user:
                user.plan = "premium"
                user.stripe_customer_id = checkout.customer
                user.stripe_subscription_id = checkout.subscription
                db.session.commit()
        except Exception as e:
            print(f"[STRIPE SUCCESS ERROR] {e}")
    return render_template("upgrade_success.html")


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    sig = request.headers.get("Stripe-Signature")
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        user = User.query.filter_by(stripe_subscription_id=sub["id"]).first()
        if user:
            user.plan = "free"
            db.session.commit()
            print(f"[STRIPE] {user.email} се върна към Free план")

    return jsonify({"received": True})


@app.route("/admin")
def admin():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")
    return render_template("admin.html")


@app.route("/api/admin/stats")
def admin_stats():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    from database import Product
    users = User.query.order_by(User.created_at.desc()).limit(50).all()
    products = Product.query.order_by(Product.last_scraped.desc()).limit(30).all()
    return jsonify({
        "total_users": User.query.count(),
        "premium_users": User.query.filter_by(plan="premium").count(),
        "total_products": Product.query.count(),
        "users": [{
            "email": u.email,
            "plan": u.plan,
            "wishlist_count": len(u.wishlists),
            "created_at": u.created_at.strftime("%d.%m.%Y") if u.created_at else ""
        } for u in users],
        "products": [{
            "name": p.name,
            "emoji": p.emoji,
            "store": p.store,
            "current_price": p.current_price,
            "last_scraped": p.last_scraped.strftime("%d.%m %H:%M") if p.last_scraped else None
        } for p in products]
    })


@app.route("/api/admin/test-email", methods=["POST"])
def admin_test_email():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    try:
        send_price_alert(data.get("email"), [{
            "name": "Мляко 3.6% Danone 1L",
            "emoji": "🥛",
            "store": "Lidl",
            "old_price": 2.49,
            "new_price": 1.99,
        }])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/unsubscribe")
def unsubscribe():
    user_id = session.get("user_id")
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.notifications_enabled = False
            db.session.commit()
    return render_template("unsubscribe.html")


# ── Старт ──────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    from database import seed_demo_data
    seed_demo_data()

scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
scheduler_thread.start()

    # Стартирай планировщика в background
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # Стартирай сървъра
    print("\n" + "="*50)
    print("  ЦениBG стартира на http://localhost:5000")
    print("="*50 + "\n")
    app.run(debug=True, use_reloader=False, host="0.0.0.0", port=5000)
