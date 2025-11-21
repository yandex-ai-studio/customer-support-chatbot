# DynamoDB Module

Модуль для персистентного хранения данных авиакомпании в AWS DynamoDB и совместимых API (Yandex Cloud Document API).

## 📁 Структура

```
app/dynamodb/
├── __init__.py            # Публичный API модуля
├── airline_state.py       # DynamoDB-backed реализация AirlineStateManager
├── utils.py              # Утилиты сериализации/десериализации
├── yandex_iam.py         # Интеграция с Yandex Cloud IAM
└── manage_airline_db.py  # Скрипт управления таблицами
```

## 🚀 Использование

### Импорт

```python
from app.dynamodb import DynamoDBAirlineStateManager

# Создание state manager
manager = DynamoDBAirlineStateManager(
    region_name="us-east-1",
    table_prefix="airline",
    endpoint_url="https://..."  # Опционально, для Yandex Cloud
)

# Создание таблицы
manager.create_table()

# Работа с профилями
profile = manager.get_profile("profile_id")
manager.change_seat("profile_id", "OA476", "12C")
```

## 🗃️ Схема таблицы

### airline_profiles

Хранит профили клиентов с информацией о рейсах, багаже и предпочтениях.

**Схема:**
- **Primary Key**: `profile_id` (String) - идентификатор профиля
- **Attributes**: 
  - `data` (Map) - сериализованный CustomerProfile
  - Включает: customer_id, name, loyalty_status, segments, bags_checked, meal_preference, special_assistance, timeline

**Пример данных:**
```python
{
    "profile_id": "demo_default_profile",
    "data": {
        "customer_id": "cus_98421",
        "name": "Jordan Miles",
        "loyalty_status": "Aviator Platinum",
        "loyalty_id": "APL-204981",
        "email": "jordan.miles@example.com",
        "phone": "+1 (415) 555-9214",
        "tier_benefits": [...],
        "segments": [
            {
                "flight_number": "OA476",
                "date": "2025-10-02",
                "origin": "SFO",
                "destination": "JFK",
                "seat": "14A",
                "status": "Scheduled"
            }
        ],
        "bags_checked": 2,
        "meal_preference": "vegetarian",
        "special_assistance": null,
        "timeline": [...]
    }
}
```

## ⚙️ Конфигурация

### Переменные окружения

```bash
# Основные настройки
USE_MEMORY_STORE=false           # Использовать DynamoDB вместо памяти
AWS_REGION=us-east-1             # AWS регион
DYNAMODB_TABLE_PREFIX=airline    # Префикс для таблиц
AUTO_CREATE_TABLES=true          # Автоматически создавать таблицы

# AWS credentials
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

# Для локального DynamoDB
DYNAMODB_ENDPOINT_URL=http://localhost:8000
```

### Пример в коде

```python
import os
from app.dynamodb import DynamoDBAirlineStateManager

manager = DynamoDBAirlineStateManager(
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    table_prefix=os.getenv("DYNAMODB_TABLE_PREFIX", "airline"),
    endpoint_url=os.getenv("DYNAMODB_ENDPOINT_URL"),
)

if os.getenv("AUTO_CREATE_TABLES", "false").lower() == "true":
    manager.create_table()
```

## 🛠️ Управление таблицами

### Через скрипт

```bash
# Создать таблицу
python -m app.dynamodb.manage_airline_db --create

# Показать статус
python -m app.dynamodb.manage_airline_db --status

# Список профилей
python -m app.dynamodb.manage_airline_db --list

# Статистика
python -m app.dynamodb.manage_airline_db --stats

# Удалить таблицу (⚠️ осторожно!)
python -m app.dynamodb.manage_airline_db --delete
```

### Программно

```python
manager = DynamoDBAirlineStateManager(...)

# Создать таблицу
manager.create_table()

# Проверить существование
if manager.table_exists():
    print("Table exists")

# Удалить таблицу
manager.delete_table()
```

## 🌐 Yandex Cloud Document API

Модуль поддерживает Yandex Cloud Document API (DynamoDB-совместимый сервис).

### Настройка

```bash
# Yandex Cloud настройки
AWS_REGION=ru-central1
DYNAMODB_ENDPOINT_URL=https://docapi.serverless.yandexcloud.net/ru-central1/xxxxx
AWS_ACCESS_KEY_ID=your_static_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### IAM токены

Модуль автоматически обрабатывает IAM токены для Yandex Cloud:

```python
from app.dynamodb.yandex_iam import is_yandex_cloud, setup_yandex_auth

# Проверка, используется ли Yandex Cloud
if is_yandex_cloud():
    print("Using Yandex Cloud")

# IAM auth настраивается автоматически в DynamoDBAirlineStateManager
```

## 📊 Примеры операций

### Получение профиля

```python
profile = manager.get_profile("profile_123")
print(f"Customer: {profile.name}")
print(f"Flights: {len(profile.segments)}")
```

### Изменение места

```python
result = manager.change_seat("profile_123", "OA476", "15A")
# "Seat updated to 15A on flight OA476."
```

### Отмена поездки

```python
result = manager.cancel_trip("profile_123")
# Все сегменты будут иметь status="Cancelled"
```

### Добавление багажа

```python
result = manager.add_bag("profile_123")
# bags_checked увеличится на 1
```

## 🧪 Тестирование

### Локальный DynamoDB

```bash
# Запустить локальный DynamoDB в Docker
docker run -p 8000:8000 amazon/dynamodb-local

# Настроить подключение
export DYNAMODB_ENDPOINT_URL=http://localhost:8000
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=dummy
export AWS_SECRET_ACCESS_KEY=dummy

# Создать таблицу
python -m app.dynamodb.manage_airline_db --create
```

## 🔒 Безопасность

### Best Practices

1. **Не храните credentials в коде** - используйте переменные окружения
2. **Используйте IAM роли** в продакшене (AWS ECS, Lambda, EC2)
3. **Ограничьте доступ** через IAM политики
4. **Включите encryption at rest** в настройках таблицы
5. **Используйте VPC endpoints** для приватного доступа

### IAM Policy пример

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/airline_*"
    }
  ]
}
```

## 📚 Дополнительная документация

- [EXAMPLES.md](./EXAMPLES.md) - Примеры использования
- [../../ARCHITECTURE.md](../../ARCHITECTURE.md) - Архитектура сервиса
- [../../README.md](../../README.md) - Основная документация
