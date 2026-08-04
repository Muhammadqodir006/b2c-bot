# b2c-bot
# Salon Bron Bot — B2C

Online navbat/bron olish tizimi — Telegram bot (mijozlar uchun).

## Talab qilinadigan dasturlar

- Python 3.10+
- Docker (Postgres uchun)

## O'rnatish

### 1. Repositoryni clone qilish

​```bash
git clone https://github.com/Muhammadqodir006/b2c-bot.git
cd b2c-bot
​```

### 2. Virtual environment yaratish

​```bash
python3 -m venv venv
source venv/bin/activate
​```

Windows'da (agar WSL ishlatmasangiz): `venv\Scripts\activate`

### 3. Kutubxonalarni o'rnatish

​```bash
pip install -r requirements.txt
​```

### 4. `.env` faylini yaratish

​```bash
cp .env.example .env
​```

Ichidagi qiymatlarni o'zgartirish shart emas — mahalliy (localhost) Postgres uchun namuna qiymatlar yetarli.

### 5. Docker o'rnatish (agar hali yo'q bo'lsa)

​```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo service docker start
​```

### 6. Postgres konteynerini ishga tushirish

​```bash
docker run -d --name salon-postgres -e POSTGRES_USER=salon_user -e POSTGRES_PASSWORD=12345678 -e POSTGRES_DB=salon_db -p 5432:5432 postgres:16
​```

Tekshirish:

​```bash
docker ps
​```

`salon-postgres` "Up" holatida ko'rinishi kerak.

### 7. Jadvallarni yaratish (migratsiya)

​```bash
alembic upgrade head
​```

### 8. Botni ishga tushirish

​```bash
python bot.py
​```

## Har safar ishni boshlashda (kompyuter qayta yoqilgandan keyin)

​```bash
sudo service docker start
docker start salon-postgres
source venv/bin/activate
​```

## Loyiha strukturasi

​```
├── bot.py                  # Kirish nuqtasi
├── config.py                # Sozlamalar (.env o'qiydi)
├── database/
│   ├── models.py             # SQLAlchemy modellar
│   └── repositories/         # DB CRUD funksiyalari
├── handlers/                 # Bot handlerlari (feature bo'yicha)
├── services/                 # Biznes logika
├── states/                   # FSM holatlar
├── keyboards/                 # Klaviaturalar
├── scheduler/                 # Eslatma tizimi
└── migrations/                 # Alembic migratsiyalari
​```

## Git ish jarayoni

- Har kim o'z branch'ida ishlaydi: `feature/<modul-nomi>` (masalan `feature/booking-flow`)
- Ishni tugatgach GitHub'da Pull Request oching
- Lider ko'rib chiqib, "Squash and merge" qiladi

## Muammo chiqsa

Manga yozing