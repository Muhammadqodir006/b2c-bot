Online navbat/bron olish tizimi — sartaroshxona, go'zallik saloni va shunga o'xshash joylar uchun. Ikkita Telegram bot: mijozlar uchun (B2C) va ustalar uchun (B2B), bitta umumiy ma'lumotlar bazasi.

Talab qilinadigan dasturlar
Python 3.10+
Docker (PostgreSQL uchun)
Git
1. Repositoryni clone qilish
bash
git clone https://github.com/Muhammadqodir006/b2c-bot.git
cd b2c-bot
2. Docker o'rnatish (agar hali yo'q bo'lsa)

WSL Ubuntu / Linux uchun:

bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

O'rnatilgach, Docker daemon'ni ishga tushiring:

bash
sudo service docker start

Tekshirish:

bash
docker --version
docker ps

Agar xatosiz, bo'sh jadval chiqsa — tayyor.

Eslatma: WSL'da systemd yo'qligi sababli, har safar yangi terminal ochganingizda sudo service docker start buyrug'ini qayta berish kerak bo'ladi (agar avtomatlashtirilmagan bo'lsa).

3. Virtual environment yaratish
bash
python3 -m venv venv
source venv/bin/activate

Terminal boshida (venv) chiqishi kerak.

4. Kutubxonalarni o'rnatish
bash
pip install -r requirements.txt
5. .env faylini yaratish
bash
cp .env.example .env

Faylni oching va quyidagi qiymatlarni to'ldiring:

DB_USER=salon_user
DB_PASSWORD=12345678
DB_HOST=localhost
DB_PORT=5432
DB_NAME=salon_db

CLIENT_BOT_TOKEN=your_client_bot_token_here
MASTER_BOT_TOKEN=your_master_bot_token_here

Bot tokenlarni qanday olish: Telegram'da @BotFather'ga /newbot yuboring, ko'rsatmalarga amal qiling. Ikkita bot kerak — biri mijozlar (client), biri ustalar (master) uchun.

DB qiymatlarini o'zgartirish shart emas — mahalliy (localhost) Postgres uchun namuna qiymatlar yetarli, faqat bot tokenlarni o'zingiznikiga almashtiring.

6. PostgreSQL'ni ishga tushirish (docker-compose orqali)

Loyihada docker-compose.yml fayli tayyor — Postgres konteynerini boshqaradi.

bash
docker compose up -d

Tekshirish:

bash
docker ps

salon-postgres nomli konteyner "Up" holatida ko'rinishi kerak, portlar ustunida 0.0.0.0:5432->5432/tcp chiqishi kerak.

Agar 5432-port band bo'lsa xato chiqsa — kompyuteringizda mahalliy Postgres o'rnatilgan bo'lishi mumkin. Uni to'xtating:

bash
sudo service postgresql stop

va docker compose up -dni qayta ishga tushiring.

7. Ma'lumotlar bazasi jadvallarini yaratish (migratsiya)
bash
alembic upgrade head

Tekshirish uchun, bazaga to'g'ridan-to'g'ri kirib ko'rish mumkin:

bash
docker exec -it salon-postgres psql -U salon_user -d salon_db -c "\dt"

Barcha jadvallar (users, salons, categories, services, masters, bookings, reviews) ko'rinishi kerak.

8. Boshlang'ich ma'lumot (seed data)

Botlarni to'liq sinash uchun kamida bitta kategoriya, salon, usta va xizmat kerak. Buni test skripti orqali qo'shish mumkin — lider (Muhammad Qodir)dan so'rang yoki docs/ papkasida seed skript bo'lsa, shuni ishga tushiring.

9. Botlarni ishga tushirish

Ikkala bot alohida jarayon sifatida ishga tushadi, ikkita alohida terminalda:

Mijoz boti (B2C):

bash
python3 bot_client.py

Usta boti (B2B):

bash
python3 bot_master.py

Har ikkalasi ham INFO:aiogram.dispatcher:Start polling xabarini ko'rsatishi kerak — bu botlar ishga tushganini bildiradi.

Har safar ishni boshlashda (kompyuter qayta yoqilgandan keyin)
bash
sudo service docker start
docker compose up -d
source venv/bin/activate

Shundan keyin bot_client.py va bot_master.pyni istalgan tartibda ishga tushirishingiz mumkin.

Loyiha strukturasi
salon_bot/
├── bot_client.py              # Mijoz bot — kirish nuqtasi
├── bot_master.py              # Usta bot — kirish nuqtasi
├── config.py                  # Sozlamalar (.env o'qiydi)
├── docker-compose.yml         # PostgreSQL konteyneri
├── requirements.txt
├── .env.example
│
├── database/
│   ├── engine.py               # Async engine, session factory
│   ├── models.py                # SQLAlchemy modellar
│   └── repositories/            # DB CRUD funksiyalari
│       ├── user_repo.py
│       ├── salon_repo.py
│       ├── booking_repo.py
│       └── review_repo.py
│
├── handlers/
│   ├── client/                   # Mijoz bot handler'lari
│   │   ├── onboarding.py
│   │   ├── main_menu.py
│   │   ├── booking_flow.py
│   │   ├── my_bookings.py
│   │   ├── review.py
│   │   └── profile.py
│   └── master/                    # Usta bot handler'lari
│       ├── onboarding.py
│       ├── profile.py
│       ├── schedule.py
│       └── notifications.py
│
├── keyboards/
│   ├── client/
│   └── master/
│
├── services/                       # Biznes logika
│   ├── booking_service.py
│   ├── salon_service.py
│   ├── geo_service.py
│   └── time_service.py             # UTC ↔ Toshkent vaqti aylantirish
│
├── states/
│   └── booking_states.py
│
├── scheduler/
│   └── reminders.py                # Eslatma xabarlari (APScheduler)
│
└── migrations/                       # Alembic
Muhim texnik qoidalar (jamoa uchun)
Til qo'llab-quvvatlash

Har bir xabar foydalanuvchi/usta tiliga (user.language yoki master.language) qarab uz/ru bo'lishi kerak. Faqat bitta tilda qattiq yozilgan matn qoldirmang.

Vaqt zonasi

Bazada barcha vaqtlar UTC formatida saqlanadi. Foydalanuvchiga ko'rsatishdan oldin services/time_service.pydagi to_local() bilan Toshkent vaqtiga aylantiring, bazaga yozishdan oldin to_utc() bilan UTC'ga aylantiring.

Router nomi

Har bir handler faylida router = Router() nomli o'zgaruvchi bo'lishi shart — bot_client.py/bot_master.py shu nom orqali ulaydi.

Band vaqt statuslari

Bron vaqtini "band" deb hisoblashda pending, confirmed, va blocked statuslari hisobga olinadi (cancelled, no_show, completed — band emas).

Git ish jarayoni
Har kim o'z branch'ida ishlaydi: feature/<modul-nomi> (masalan feature/booking-flow)
Ishni tugatgach GitHub'da Pull Request oching
Lider ko'rib chiqib, "Squash and merge" qiladi
Muammo chiqsa

