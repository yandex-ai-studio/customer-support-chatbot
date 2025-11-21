# Примеры использования модуля DynamoDB

Этот модуль предоставляет DynamoDB-backed Store для ChatKit.

## 🎯 Быстрый старт

### Базовая настройка

```python
import os
from app.dynamodb import DynamoDBStore

# Установка переменных окружения
os.environ['USE_MEMORY_STORE'] = 'false'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['DYNAMODB_TABLE_PREFIX'] = 'chatkit'
os.environ['DYNAMODB_ENDPOINT_URL'] = 'https://...'  # Для Yandex Cloud

# Создание store
store = DynamoDBStore(
    region_name=os.environ['AWS_REGION'],
    table_prefix=os.environ['DYNAMODB_TABLE_PREFIX'],
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT_URL')
)

# Создание таблиц (если ещё не созданы)
store.create_tables()
```

## 📝 Работа с ChatKit Store

### Создание и загрузка threads

```python
from chatkit.types import Thread, ThreadMetadata
from datetime import datetime

# Создание thread
thread = Thread(
    id="thread_123",
    title="Customer Support",
    created_at=datetime.now(),
    updated_at=datetime.now(),
)

# Сохранение thread
await store.save_thread(thread, context={})

# Загрузка thread
loaded_thread = await store.load_thread("thread_123", context={})
print(f"Thread: {loaded_thread.title}")

# Удаление thread
await store.delete_thread("thread_123", context={})
```

### Работа с сообщениями

```python
from chatkit.types import UserMessageItem, TextContentBlock
import uuid

# Создание сообщения
message_item = UserMessageItem(
    id=str(uuid.uuid4()),
    content=[TextContentBlock(text="Hello, I need help!")],
    created_at=datetime.now(),
)

# Добавление сообщения в thread
await store.add_thread_item("thread_123", message_item, context={})

# Загрузка сообщений thread
items = await store.load_thread_items(
    thread_id="thread_123",
    before=None,
    limit=20,
    order="desc",
    context={}
)

for item in items.items:
    print(f"Message: {item.id}")
```


## 🔧 Использование утилит сериализации

### Базовая сериализация

```python
from app.dynamodb import serialize_for_dynamodb, deserialize_from_dynamodb
from datetime import datetime
from decimal import Decimal

# Сериализация различных типов
data = {
    'string': 'Hello',
    'integer': 42,
    'float': 3.14159,
    'boolean': True,
    'datetime': datetime(2025, 1, 1, 12, 0, 0),
    'list': [1, 2, 3],
    'nested': {
        'value': 99.99,
        'items': ['a', 'b', 'c']
    }
}

# Преобразование для DynamoDB
serialized = serialize_for_dynamodb(data)

print(type(serialized['float']))      # <class 'decimal.Decimal'>
print(type(serialized['datetime']))   # <class 'str'>
print(serialized['datetime'])         # '2025-01-01T12:00:00'

# Обратное преобразование
deserialized = deserialize_from_dynamodb(serialized)

print(type(deserialized['float']))    # <class 'float'>
print(deserialized['float'])          # 3.14159
```

### Работа со сложными структурами

```python
# Сложная структура данных
complex_data = {
    'user': {
        'id': 12345,
        'balance': 1599.99,
        'registered': datetime.now(),
        'tags': {'premium', 'verified', 'active'},
        'preferences': {
            'theme': 'dark',
            'notifications': True,
            'limits': [100.0, 500.0, 1000.0]
        }
    }
}

# Сериализация (рекурсивная обработка)
serialized = serialize_for_dynamodb(complex_data)

# set преобразован в list
print(type(serialized['user']['tags']))  # <class 'list'>

# float преобразован в Decimal (вложенный)
limits = serialized['user']['preferences']['limits']
print(all(isinstance(x, Decimal) for x in limits))  # True

# Десериализация восстанавливает типы
deserialized = deserialize_from_dynamodb(serialized)
print(type(deserialized['user']['balance']))  # <class 'float'>
```

## 🧪 Интеграция с FastAPI

### Использование в endpoint

```python
from fastapi import FastAPI, Depends
from app.dynamodb import DynamoDBStore
from chatkit.server import ChatKitServer

app = FastAPI()


# Dependency injection
def get_store() -> DynamoDBStore:
    return DynamoDBStore(region_name='us-east-1')


# Используется в ChatKitServer
chatkit_server = ChatKitServer(store=get_store())
```

## 🔍 Управление через CLI

### Создание таблиц

```bash
cd chatkit-agent

# Создание всех таблиц
python scripts/manage_dynamodb.py --create

# Проверка статуса
python scripts/manage_dynamodb.py --status
```

### Просмотр данных

```bash
# Список threads
python scripts/manage_dynamodb.py --list-threads

# Список профилей
python scripts/manage_dynamodb.py --list-profiles

# Детальная статистика
python scripts/manage_dynamodb.py --stats
```

### Удаление данных

```bash
# Удаление всех таблиц (требует подтверждения)
python scripts/manage_dynamodb.py --delete
```

## 🐛 Отладка

### Проверка подключения

```python
import boto3
from botocore.exceptions import ClientError

def test_connection(endpoint_url: str, region: str = 'us-east-1'):
    """Проверка подключения к DynamoDB"""
    try:
        client = boto3.client(
            'dynamodb',
            region_name=region,
            endpoint_url=endpoint_url
        )
        
        # Попытка получить список таблиц
        response = client.list_tables()
        print(f"✅ Подключение успешно")
        print(f"   Найдено таблиц: {len(response['TableNames'])}")
        return True
        
    except ClientError as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

# Использование
test_connection('https://docapi.serverless.yandexcloud.net/...')
```

### Логирование операций

```python
import logging

# Включение debug логов для boto3
logging.basicConfig(level=logging.DEBUG)
boto3.set_stream_logger('boto3.resources', logging.DEBUG)

# Теперь все операции с DynamoDB будут логироваться
store = DynamoDBStore(region_name='us-east-1')
# ... операции ...
```

## 📚 См. также

- [DynamoDB Module README](./README.md)
- [ChatKit Python Documentation](https://openai.github.io/chatkit-python/)
- [AWS SDK for Python (Boto3)](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

