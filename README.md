# Telegram-бот приёма заявок — «Мастер Дом»

Демо-проект для портфолио: бот принимает заявки на ремонт квартир для вымышленной компании «Мастер Дом» и передаёт их администратору.

**Стек:** Python 3.11+, aiogram 3, SQLite (aiosqlite), python-dotenv.

## Возможности

**Для клиента**
- `/start` — приветствие и меню: «Услуги и цены», «Наши работы», «Частые вопросы», «Контакты», «Оставить заявку».
- Заявка по шагам: тип работ (кнопки) → описание → фото (можно пропустить) → телефон (кнопка «Отправить номер» или вручную) → удобное время звонка → подтверждение.
- Отмена на любом шаге — кнопка «Отменить» или `/cancel`.
- Уведомление, когда статус заявки меняется.

**Для администратора** (личный чат или группа)
- Каждая заявка приходит карточкой (с фото, если оно есть) и кнопками «Взять в работу», «Закрыть», «Отклонить». После нажатия карточка обновляется: новый статус и кто его поменял.
- `/stats` — заявки за сегодня, за 7 дней, всего и по статусам.
- `/export` — все заявки CSV-файлом прямо в чат (UTF-8 с BOM, разделитель `;` — открывается в Excel без настроек).

## Структура

```
bot.py              точка входа
config.py           всё, что зависит от клиента: тексты, услуги, цены, FAQ, контакты, статусы
settings.py         чтение .env
db.py               работа с SQLite
keyboards.py        клавиатуры
states.py           шаги заявки (FSM)
handlers/
  client.py         меню и информационные разделы
  order.py          оформление заявки
  admin.py          статусы, /stats, /export
services/notify.py  карточка для админа и уведомления клиенту
deploy/             пример systemd-юнита
```

## Адаптация под нового клиента

Менять нужно только `config.py`: название компании, услуги и цены, портфолио, вопросы-ответы, контакты, типы работ, варианты времени звонка, тексты сообщений и уведомлений.

## Локальный запуск

1. Создайте бота у [@BotFather](https://t.me/BotFather) и получите токен.
2. Узнайте ID чата для заявок:
   - личный чат — напишите [@userinfobot](https://t.me/userinfobot);
   - группа — добавьте бота в группу и, например, [@getmyid_bot](https://t.me/getmyid_bot); ID группы отрицательный (`-100…`).
3. Установите зависимости и настройте окружение:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # впишите BOT_TOKEN и ADMIN_CHAT_ID
python bot.py
```

База `requests.db` создаётся автоматически при первом запуске.

> Если заявки приходят в группу, добавьте туда бота. Нажатия кнопок и команды `/stats`, `/export` принимаются только из чата `ADMIN_CHAT_ID`.

## Деплой на сервер через systemd

Пример для Ubuntu/Debian:

```bash
# 1. Пользователь и код
sudo useradd --system --create-home --shell /usr/sbin/nologin bot
sudo git clone https://github.com/vit3ma3/application_intake_demo.git /opt/masterdom-bot
sudo chown -R bot:bot /opt/masterdom-bot

# 2. Окружение
cd /opt/masterdom-bot
sudo -u bot python3 -m venv .venv
sudo -u bot .venv/bin/pip install -r requirements.txt
sudo -u bot cp .env.example .env
sudo -u bot nano .env          # BOT_TOKEN, ADMIN_CHAT_ID
sudo chmod 600 .env

# 3. Сервис
sudo cp deploy/masterdom-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now masterdom-bot
```

Управление:

```bash
sudo systemctl status masterdom-bot     # состояние
sudo journalctl -u masterdom-bot -f     # логи
sudo systemctl restart masterdom-bot    # перезапуск после изменений
```

Обновление:

```bash
cd /opt/masterdom-bot
sudo -u bot git pull
sudo -u bot .venv/bin/pip install -r requirements.txt
sudo systemctl restart masterdom-bot
```

Бэкап — достаточно копировать файл `requests.db`.
