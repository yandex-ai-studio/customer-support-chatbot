# DynamoDB Module

Модуль для работы с AWS DynamoDB и совместимыми API (Yandex Cloud Document API) для ChatKit Store.

## 📁 Структура

```
app/dynamodb/
├── __init__.py         # Публичный API модуля
├── utils.py           # Утилиты сериализации/десериализации
├── store.py           # ChatKit Store implementation
└── yandex_iam.py      # Yandex Cloud IAM integration
```

## 🚀 Использование

### Импорт через модуль

```python
# Рекомендуемый способ - импорт через модуль
from app.dynamodb import (
    DynamoDBStore,
    serialize_for_dynamodb,
    deserialize_from_dynamodb,
)
```

### Создание Store

```python
from app.dynamodb import DynamoDBStore

store = DynamoDBStore(
    region_name="us-east-1",
    table_prefix="chatkit",
    endpoint_url="https://..."  # Опционально, для non-AWS endpoints
)

# Создание таблиц
store.create_tables()

# Работа с threads
thread = await store.load_thread("thread_id", context={})
```

### Использование утилит

```python
from app.dynamodb import serialize_for_dynamodb, deserialize_from_dynamodb
from datetime import datetime

# Сериализация
data = {
    "price": 99.99,
    "timestamp": datetime.now(),
    "items": [1, 2, 3]
}
serialized = serialize_for_dynamodb(data)
# Готово для DynamoDB: float → Decimal, datetime → ISO string

# Десериализация
retrieved = deserialize_from_dynamodb(serialized)
# Обратно в Python типы: Decimal → float/int
```

## 📦 Компоненты

### `utils.py`
- **`serialize_for_dynamodb(obj)`** - Конвертация Python → DynamoDB
- **`deserialize_from_dynamodb(obj)`** - Конвертация DynamoDB → Python

Автоматически обрабатывает:
- `float` → `Decimal` (и обратно)
- `datetime` → ISO string
- `set` → `list`
- Рекурсивная обработка `dict`, `list`, `tuple`

### `store.py`
**`DynamoDBStore`** - реализация ChatKit Store для DynamoDB

Таблицы:
- `chatkit_threads` - метаданные threads
- `chatkit_thread_items` - сообщения и события
- `chatkit_attachments` - метаданные файлов

Методы:
- `create_tables()` - создание таблиц
- `delete_tables()` - удаление таблиц
- `load_thread()`, `save_thread()`, `delete_thread()`
- `load_thread_items()`, `add_thread_item()`
- `load_attachment()`, `save_attachment()`

### `yandex_iam.py`
Утилиты для интеграции с Yandex Cloud IAM и Document API:
- `is_yandex_cloud()` - проверка использования Yandex Cloud
- `setup_yandex_auth()` - настройка IAM авторизации
- `get_yandex_boto_config()` - конфигурация boto3 для Yandex Cloud

## 🔧 Конфигурация

Переменные окружения:
```bash
USE_MEMORY_STORE=false                    # Включить DynamoDB
AWS_REGION=us-east-1                     # AWS регион
DYNAMODB_TABLE_PREFIX=chatkit            # Префикс таблиц
DYNAMODB_ENDPOINT_URL=https://...        # Кастомный endpoint
AUTO_CREATE_TABLES=true                  # Авто-создание таблиц
```

## 🧪 Тестирование

```bash
# Проверка импортов
python -c "from app.dynamodb import DynamoDBStore; print('✅ OK')"

# Запуск скрипта управления
python scripts/manage_dynamodb.py --status
```

## 📚 См. также

- [ChatKit Python Documentation](https://openai.github.io/chatkit-python/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Yandex Cloud Document API](https://cloud.yandex.ru/docs/ydb/docapi/api-ref/)

