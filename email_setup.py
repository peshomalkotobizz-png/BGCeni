"""
ЦениBG — Gmail настройка и тест на имейл
Стартирай: python email_setup.py
"""

import os
import sys


def setup_email():
    print("""
╔══════════════════════════════════════════════════════════╗
║  ЦениBG — Настройка на имейл нотификации                ║
╚══════════════════════════════════════════════════════════╝
    """)

    print("""СТЪПКИ за Gmail:

  1. Отиди на: https://myaccount.google.com/security
  2. Включи "2-Step Verification" (ако не е включено)
  3. Отиди на: https://myaccount.google.com/apppasswords
  4. Избери: "Mail" → "Windows Computer"
  5. Кликни "Generate"
  6. Ще получиш парола от 16 символа (xxxx xxxx xxxx xxxx)
     Копирай я БЕЗ интервалите
    """)

    gmail = input("Gmail адрес (напр. cenibg@gmail.com): ").strip()
    app_pass = input("App Password (16 символа без интервали): ").strip().replace(" ", "")

    if len(app_pass) != 16:
        print(f"⚠ Очаквам 16 символа, получих {len(app_pass)}. Провери паролата.")

    # Тест на имейла
    print(f"\n→ Тествам изпращане до {gmail}...")

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "✅ ЦениBG — имейлът работи!"
        msg["From"] = gmail
        msg["To"] = gmail

        html = """
        <div style="background:#0a0a0f;font-family:Inter,sans-serif;padding:40px;max-width:500px;margin:0 auto;border-radius:16px">
          <div style="font-size:24px;font-weight:900;color:#e8ff00;margin-bottom:8px">ЦениBG</div>
          <h2 style="color:#f0f0f8">✅ Имейлът работи!</h2>
          <p style="color:#6b6b8a;line-height:1.8">
            Нотификациите са настроени. Ще получаваш имейли като този когато
            продукт от твоя Wishlist поевтинее.
          </p>
          <div style="background:#1a1a26;border-radius:10px;padding:1rem;margin-top:1.5rem">
            <div style="color:#e8ff00;font-weight:700;margin-bottom:.5rem">🔔 Пример за намаление:</div>
            <div style="color:#f0f0f8">Мляко Danone 1L — <span style="text-decoration:line-through;color:#6b6b8a">2.49 лв.</span> → <span style="color:#4cff6e;font-weight:700">1.99 лв.</span> (спестяваш 20%)</div>
          </div>
        </div>"""

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(gmail, app_pass)
            server.sendmail(gmail, gmail, msg.as_string())

        print(f"✓ Тестов имейл изпратен до {gmail}!")
        print("  Провери входящата си поща (или Спам).\n")

        # Запиши в .env
        from stripe_setup import update_env
        update_env("MAIL_USERNAME", gmail)
        update_env("MAIL_PASSWORD", app_pass)
        print("✓ Gmail данните са записани в .env\n")

    except Exception as e:
        print(f"✗ Грешка: {e}")
        print("\nЧести причини:")
        print("  • App Password е грешен — генерирай нов от Google")
        print("  • 2-Step Verification не е включен")
        print("  • Опитваш с обичайната парола вместо App Password\n")
        return False

    print("""
╔══════════════════════════════════════════════════════════╗
║  ✅ Имейлът е настроен! Рестартирай: start.bat           ║
╚══════════════════════════════════════════════════════════╝
    """)
    return True


if __name__ == "__main__":
    setup_email()
