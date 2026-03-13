"""
ЦениBG — Stripe автоматична настройка
Стартирай: python stripe_setup.py
Ще създаде продукта и ценовия план в Stripe автоматично.
"""

import os
import sys

def setup_stripe():
    # Зареди .env
    if os.path.exists(".env"):
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip()

    try:
        import stripe
    except ImportError:
        print("Инсталирам stripe...")
        os.system("pip install stripe -q")
        import stripe

    secret_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not secret_key or "ЗАМЕНИ" in secret_key or not secret_key.startswith("sk_"):
        print("""
╔══════════════════════════════════════════════════════════╗
║  СТЪПКА 1: Вземи Stripe API ключовете                   ║
╠══════════════════════════════════════════════════════════╣
║                                                          ║
║  1. Отиди на: https://dashboard.stripe.com               ║
║  2. Регистрирай се (безплатно)                           ║
║  3. Developers → API keys                               ║
║  4. Копирай:                                             ║
║     • Publishable key  (pk_test_...)                     ║
║     • Secret key       (sk_test_...)                     ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
        """)
        secret_key = input("Постави Secret key (sk_test_...): ").strip()
        pub_key = input("Постави Publishable key (pk_test_...): ").strip()

        # Запиши в .env
        update_env("STRIPE_SECRET_KEY", secret_key)
        update_env("STRIPE_PUBLISHABLE_KEY", pub_key)
        print("✓ Ключовете са записани в .env\n")

    stripe.api_key = secret_key

    # Провери връзката
    try:
        stripe.Account.retrieve()
        print("✓ Stripe връзка: OK\n")
    except stripe.error.AuthenticationError:
        print("✗ Невалиден API ключ! Провери го и опитай пак.")
        sys.exit(1)

    # Провери дали продуктът вече съществува
    existing = stripe.Product.list(limit=10)
    cenibg_product = None
    for prod in existing.data:
        if "ЦениBG" in prod.name or "CeniBG" in prod.name:
            cenibg_product = prod
            break

    if cenibg_product:
        print(f"✓ Продукт вече съществува: {cenibg_product.name} ({cenibg_product.id})")
    else:
        print("→ Създавам продукт в Stripe...")
        cenibg_product = stripe.Product.create(
            name="ЦениBG Premium",
            description="Неограничено следене на цени в Lidl, Kaufland и Billa. Имейл нотификации при намаления.",
        )
        print(f"✓ Продукт създаден: {cenibg_product.id}")

    # Провери за съществуваща цена
    existing_prices = stripe.Price.list(product=cenibg_product.id, limit=5)
    cenibg_price = None
    for price in existing_prices.data:
        if price.unit_amount == 400 and price.currency == "bgn":
            cenibg_price = price
            break

    if cenibg_price:
        print(f"✓ Цена вече съществува: {cenibg_price.id} ({cenibg_price.unit_amount/100:.2f} BGN/мес.)")
    else:
        print("→ Създавам ценови план: 4.00 BGN/мес...")
        cenibg_price = stripe.Price.create(
            product=cenibg_product.id,
            unit_amount=400,          # 400 стотинки = 4.00 лв.
            currency="bgn",
            recurring={"interval": "month"},
        )
        print(f"✓ Ценови план създаден: {cenibg_price.id}")

    # Запиши Price ID в .env
    update_env("STRIPE_PRICE_ID", cenibg_price.id)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ✅ Stripe е настроен успешно!                           ║
╠══════════════════════════════════════════════════════════╣
║  Product ID : {cenibg_product.id:<40} ║
║  Price ID   : {cenibg_price.id:<40} ║
║  Цена       : 4.00 BGN / месец                           ║
╠══════════════════════════════════════════════════════════╣
║  СТЪПКА 2: Настрой Webhook (за автоматично отписване)    ║
║                                                          ║
║  Инсталирай Stripe CLI:                                  ║
║  https://stripe.com/docs/stripe-cli#install              ║
║                                                          ║
║  После стартирай:                                        ║
║    stripe login                                          ║
║    stripe listen --forward-to localhost:5000/stripe-webhook
║                                                          ║
║  Копирай whsec_... ключа в .env                          ║
╠══════════════════════════════════════════════════════════╣
║  ТЕСТ КАРТА за проверка:                                 ║
║    Номер:  4242 4242 4242 4242                           ║
║    Дата:   12/34   CVV: 123                              ║
╚══════════════════════════════════════════════════════════╝
    """)

    print("→ Рестартирай приложението: start.bat")


def update_env(key, value):
    """Обновява стойност в .env файла."""
    env_path = ".env"
    if not os.path.exists(env_path):
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", env_path)
        else:
            open(env_path, "w").close()

    with open(env_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(key + "="):
            new_lines.append(f"{key}={value}\n")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    setup_stripe()
