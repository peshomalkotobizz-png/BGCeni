"""
ЦениBG — Deploy помощник
Качва приложението на Railway.app (безплатно)
Стартирай: python deploy.py
"""

import os
import sys
import subprocess
import shutil


def check_git():
    return shutil.which("git") is not None

def check_node():
    return shutil.which("node") is not None

def run(cmd, check=True):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"    {result.stdout.strip()}")
    if result.returncode != 0 and check:
        print(f"  ✗ Грешка: {result.stderr.strip()}")
    return result.returncode == 0


def deploy():
    print("""
╔══════════════════════════════════════════════════════════╗
║  ЦениBG — Deploy на Railway.app                         ║
║  Безплатен хостинг, 500 часа/месец                      ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Стъпка 1: Провери prerequisites
    print("→ Проверка на инструменти...")

    if not check_git():
        print("""
  ✗ Git не е инсталиран.
  Изтегли от: https://git-scm.com/download/win
  След инсталация рестартирай командния ред.
        """)
        sys.exit(1)
    print("  ✓ Git")

    # Стъпка 2: Инициализирай Git repo
    if not os.path.exists(".git"):
        print("\n→ Инициализирам Git репозитория...")
        run("git init")
        run('git config user.email "cenibg@example.com"')
        run('git config user.name "CeniBG"')

    # Стъпка 3: Създай .gitignore
    gitignore = """.env
*.db
__pycache__/
*.pyc
*.pyo
.DS_Store
venv/
env/
*.egg-info/
dist/
build/
"""
    with open(".gitignore", "w") as f:
        f.write(gitignore)
    print("  ✓ .gitignore създаден")

    # Стъпка 4: Създай Procfile (за Railway/Render)
    with open("Procfile", "w") as f:
        f.write("web: gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT\n")
    print("  ✓ Procfile създаден")

    # Стъпка 5: Добави gunicorn в requirements
    with open("requirements.txt", "r") as f:
        reqs = f.read()
    if "gunicorn" not in reqs:
        with open("requirements.txt", "a") as f:
            f.write("gunicorn==21.2.0\n")
        print("  ✓ gunicorn добавен в requirements.txt")

    # Стъпка 6: Създай runtime.txt
    with open("runtime.txt", "w") as f:
        f.write("python-3.11.0\n")
    print("  ✓ runtime.txt създаден")

    # Стъпка 7: Git commit
    print("\n→ Добавям файловете в Git...")
    run("git add -A")
    run('git commit -m "ЦениBG v1.0 — initial commit"')

    print("""
╔══════════════════════════════════════════════════════════╗
║  ✅ Подготовката е готова!                               ║
╠══════════════════════════════════════════════════════════╣
║  СЛЕДВАЩИ СТЪПКИ — качване на Railway.app:              ║
║                                                          ║
║  ВАРИАНТ А (препоръчително) — GitHub:                   ║
║  1. Качи кода на GitHub.com (безплатно)                 ║
║  2. Отиди на railway.app → New Project                  ║
║  3. Deploy from GitHub → избери репото                  ║
║  4. Add Variables → попълни от .env файла:              ║
║     SECRET_KEY, STRIPE_SECRET_KEY,                      ║
║     STRIPE_PUBLISHABLE_KEY, STRIPE_PRICE_ID,            ║
║     MAIL_USERNAME, MAIL_PASSWORD                        ║
║  5. Add Plugin → PostgreSQL (безплатна база)            ║
║     → Копирай DATABASE_URL от plugin-а                  ║
║                                                          ║
║  ВАРИАНТ Б — Railway CLI:                               ║
║  npm install -g @railway/cli                            ║
║  railway login                                          ║
║  railway init                                           ║
║  railway up                                             ║
║  railway variables set STRIPE_SECRET_KEY=sk_live_...   ║
║  railway open                                           ║
║                                                          ║
║  ДОМЕЙН: Railway дава безплатен .railway.app домейн    ║
║  За cenibg.bg → Namecheap (~10$/год) + CNAME в Railway ║
╠══════════════════════════════════════════════════════════╣
║  💡 ПРОДУКЦИОННА СРЕДА:                                 ║
║  • Смени sk_test_ с sk_live_ в Stripe                   ║
║  • Смени pk_test_ с pk_live_ в Stripe                   ║
║  • Настрой Webhook URL на реалния домейн                ║
╚══════════════════════════════════════════════════════════╝
    """)


if __name__ == "__main__":
    deploy()
