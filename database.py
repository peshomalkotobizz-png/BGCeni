"""
База данни — SQLAlchemy модели
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(200), default="")
    plan = db.Column(db.String(20), default="free")  # free | premium
    alert_threshold = db.Column(db.Integer, default=10)  # % намаление
    notifications_enabled = db.Column(db.Boolean, default=True)
    stripe_customer_id = db.Column(db.String(100))
    stripe_subscription_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wishlists = db.relationship("Wishlist", backref="user", lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    emoji = db.Column(db.String(10), default="🛒")
    store = db.Column(db.String(50), nullable=False)   # Lidl | Kaufland | Billa
    url = db.Column(db.String(500))
    current_price = db.Column(db.Float, default=0.0)
    last_scraped = db.Column(db.DateTime)

    price_history = db.relationship("PriceHistory", backref="product", lazy=True)
    wishlists = db.relationship("Wishlist", backref="product", lazy=True)


class PriceHistory(db.Model):
    __tablename__ = "price_history"
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Wishlist(db.Model):
    __tablename__ = "wishlist"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)


def seed_demo_data():
    """Попълва базата с демо продукти ако е празна."""
    if Product.query.count() > 0:
        return

    demo_products = [
        ("🥛", "Мляко 3.6% Danone 1L", "Lidl", 1.89, [2.19, 2.09, 2.19, 1.89]),
        ("🫙", "Кисело мляко Лакта 400г", "Kaufland", 1.29, [1.29, 1.49, 1.39, 1.29]),
        ("🧈", "Масло 82% 125г", "Kaufland", 2.79, [3.29, 3.29, 2.99, 2.79]),
        ("🥚", "Яйца 10 бр. М", "Billa", 3.49, [3.99, 3.79, 3.79, 3.49]),
        ("🧺", "Прах Ariel 2кг", "Lidl", 8.99, [10.99, 10.99, 9.99, 8.99]),
        ("🫙", "Слънчогледово масло 1L", "Billa", 3.19, [3.49, 3.29, 3.19, 3.19]),
        ("🍞", "Хляб Добруджа 650г", "Lidl", 1.49, [1.79, 1.79, 1.59, 1.49]),
        ("🍬", "Захар 1кг бяла", "Kaufland", 2.39, [2.39, 2.59, 2.49, 2.39]),
        ("☕", "Кафе Lavazza 250г", "Billa", 8.49, [9.99, 9.49, 8.99, 8.49]),
        ("🍅", "Доматен сок Cappy 1L", "Lidl", 1.19, [1.49, 1.39, 1.29, 1.19]),
        ("🧀", "Кашкавал Витоша 400г", "Kaufland", 6.99, [7.99, 7.49, 6.99, 6.99]),
        ("🍗", "Пилешки гърди 1кг", "Lidl", 7.49, [8.99, 8.49, 7.99, 7.49]),
        ("🧻", "Тоалетна хартия 8 ролки", "Billa", 4.99, [5.99, 5.49, 4.99, 4.99]),
        ("🫧", "Препарат за съдове 500мл", "Kaufland", 1.89, [2.29, 2.09, 1.89, 1.89]),
        ("🍫", "Шоколад Milka 100г", "Lidl", 2.19, [2.49, 2.49, 2.29, 2.19]),
        ("🍌", "Банани 1кг", "Billa", 1.99, [2.49, 2.19, 1.99, 1.99]),
        ("🥩", "Кайма свинска 500г", "Kaufland", 5.49, [6.49, 5.99, 5.49, 5.49]),
        ("🧴", "Шампоан Pantene 400мл", "Billa", 6.99, [8.49, 7.99, 6.99, 6.99]),
        ("🍪", "Бисквити Oreo 154г", "Lidl", 2.89, [3.29, 2.89, 2.89, 2.89]),
        ("🫒", "Зехтин 0.5L", "Kaufland", 9.99, [12.99, 11.49, 10.49, 9.99]),
    ]

    from datetime import timedelta
    base_date = datetime.utcnow() - timedelta(days=3)

    for emoji, name, store, current, history_prices in demo_products:
        p = Product(
            name=name,
            emoji=emoji,
            store=store,
            current_price=current,
            last_scraped=datetime.utcnow()
        )
        db.session.add(p)
        db.session.flush()

        for i, price in enumerate(history_prices):
            ph = PriceHistory(
                product_id=p.id,
                price=price,
                date=base_date + timedelta(days=i)
            )
            db.session.add(ph)

    db.session.commit()
    print("[DB] Демо данните са заредени — 20 продукта от 3 магазина")
