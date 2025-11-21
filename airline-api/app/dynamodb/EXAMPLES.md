# Примеры использования DynamoDB модуля

## 🎯 Быстрый старт

### Базовая настройка

```python
import os
from app.dynamodb import DynamoDBAirlineStateManager

# Установка переменных окружения
os.environ['USE_MEMORY_STORE'] = 'false'
os.environ['AWS_REGION'] = 'us-east-1'
os.environ['DYNAMODB_TABLE_PREFIX'] = 'airline'

# Создание state manager
manager = DynamoDBAirlineStateManager(
    region_name=os.environ['AWS_REGION'],
    table_prefix=os.environ['DYNAMODB_TABLE_PREFIX'],
    endpoint_url=os.environ.get('DYNAMODB_ENDPOINT_URL')
)

# Создание таблицы (если ещё не создана)
if not manager.table_exists():
    manager.create_table()
```

## 📝 Работа с профилями клиентов

### Получение профиля

```python
# Получить профиль (создаётся автоматически, если не существует)
profile = manager.get_profile("profile_123")

print(f"Customer: {profile.name}")
print(f"Loyalty Status: {profile.loyalty_status}")
print(f"Email: {profile.email}")
print(f"Bags: {profile.bags_checked}")
print(f"Meal Preference: {profile.meal_preference}")

# Сегменты полёта
for segment in profile.segments:
    print(f"  Flight {segment.flight_number}: {segment.origin} → {segment.destination}")
    print(f"    Seat: {segment.seat}, Status: {segment.status}")
```

### Изменение места

```python
# Изменить место на рейсе
result = manager.change_seat(
    profile_id="profile_123",
    flight_number="OA476",
    seat="12C"
)
print(result)  # "Seat updated to 12C on flight OA476."

# Проверяем обновлённый профиль
profile = manager.get_profile("profile_123")
segment = next(s for s in profile.segments if s.flight_number == "OA476")
print(f"New seat: {segment.seat}")  # 12C
```

### Добавление багажа

```python
# Добавить багаж
result = manager.add_bag("profile_123")
print(result)  # "Checked bag added. You now have 1 bag(s) checked."

# Добавить ещё
result = manager.add_bag("profile_123")
print(result)  # "Checked bag added. You now have 2 bag(s) checked."
```

### Установка предпочтения по еде

```python
# Установить предпочтение
result = manager.set_meal("profile_123", "vegetarian")
print(result)  # "We'll note vegetarian as the meal preference."

# Другие варианты
manager.set_meal("profile_123", "vegan")
manager.set_meal("profile_123", "gluten-free")
manager.set_meal("profile_123", "kosher")
```

### Запрос специальной помощи

```python
# Запросить помощь
result = manager.request_assistance(
    profile_id="profile_123",
    note="Wheelchair assistance needed at both airports"
)
print(result)  # "Assistance request recorded. Airport staff will be notified."

# Проверить в профиле
profile = manager.get_profile("profile_123")
print(profile.special_assistance)
```

### Отмена поездки

```python
# Отменить всю поездку
result = manager.cancel_trip("profile_123")
print(result)  # "The reservation has been cancelled. Refund processing will begin immediately."

# Проверить статус сегментов
profile = manager.get_profile("profile_123")
for segment in profile.segments:
    print(f"{segment.flight_number}: {segment.status}")  # Все будут "Cancelled"
```

## 📜 Работа с timeline

```python
# Timeline автоматически обновляется при каждой операции
profile = manager.get_profile("profile_123")

print("Service Timeline:")
for entry in profile.timeline[:5]:  # Последние 5 записей
    print(f"  [{entry['kind']}] {entry['timestamp']}")
    print(f"    {entry['entry']}")
```

## 🔄 Полный workflow

```python
from app.dynamodb import DynamoDBAirlineStateManager

# Инициализация
manager = DynamoDBAirlineStateManager(
    region_name="us-east-1",
    table_prefix="airline"
)

profile_id = "customer_john_doe"

# 1. Получить профиль (создаётся с дефолтными данными)
profile = manager.get_profile(profile_id)
print(f"Welcome, {profile.name}!")

# 2. Изменить место
manager.change_seat(profile_id, "OA476", "14A")

# 3. Добавить багаж
manager.add_bag(profile_id)
manager.add_bag(profile_id)

# 4. Установить предпочтение по еде
manager.set_meal(profile_id, "vegetarian")

# 5. Запросить помощь
manager.request_assistance(profile_id, "Early boarding requested")

# 6. Проверить итоговый профиль
profile = manager.get_profile(profile_id)
print(f"\nFinal Profile:")
print(f"  Name: {profile.name}")
print(f"  Bags: {profile.bags_checked}")
print(f"  Meal: {profile.meal_preference}")
print(f"  Assistance: {profile.special_assistance}")

print(f"\nFlights:")
for segment in profile.segments:
    print(f"  {segment.flight_number}: Seat {segment.seat} ({segment.status})")

print(f"\nRecent Activity:")
for entry in profile.timeline[:3]:
    print(f"  - {entry['entry']}")
```

## 🌐 REST API интеграция

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.dynamodb import DynamoDBAirlineStateManager

app = FastAPI()
manager = DynamoDBAirlineStateManager(region_name="us-east-1")

class ChangeSeatRequest(BaseModel):
    profile_id: str
    flight_number: str
    seat: str

@app.post("/seat")
def change_seat(request: ChangeSeatRequest):
    try:
        result = manager.change_seat(
            request.profile_id,
            request.flight_number,
            request.seat
        )
        return {"success": True, "message": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/profile/{profile_id}")
def get_profile(profile_id: str):
    profile = manager.get_profile(profile_id)
    return {"success": True, "profile": profile.to_dict()}
```

## 🧪 Тестирование

### Unit тесты

```python
import pytest
from app.airline_state import AirlineStateManager

def test_change_seat():
    manager = AirlineStateManager()
    
    # Получить дефолтный профиль
    profile = manager.get_profile("test_profile")
    original_seat = profile.segments[0].seat
    
    # Изменить место
    result = manager.change_seat("test_profile", "OA476", "15C")
    assert "15C" in result
    
    # Проверить обновление
    profile = manager.get_profile("test_profile")
    assert profile.segments[0].seat == "15C"
    assert profile.segments[0].seat != original_seat

def test_add_bag():
    manager = AirlineStateManager()
    
    profile = manager.get_profile("test_profile")
    original_bags = profile.bags_checked
    
    manager.add_bag("test_profile")
    
    profile = manager.get_profile("test_profile")
    assert profile.bags_checked == original_bags + 1

def test_invalid_seat():
    manager = AirlineStateManager()
    
    with pytest.raises(ValueError):
        manager.change_seat("test_profile", "OA476", "invalid")
    
    with pytest.raises(ValueError):
        manager.change_seat("test_profile", "OA476", "99")  # Нет буквы

def test_invalid_flight():
    manager = AirlineStateManager()
    
    with pytest.raises(ValueError):
        manager.change_seat("test_profile", "NOTEXIST", "12C")
```

### Integration тесты с DynamoDB

```python
import pytest
from app.dynamodb import DynamoDBAirlineStateManager

@pytest.fixture
def dynamodb_manager():
    # Использовать локальный DynamoDB для тестов
    manager = DynamoDBAirlineStateManager(
        region_name="us-east-1",
        table_prefix="test_airline",
        endpoint_url="http://localhost:8000"
    )
    manager.create_table()
    yield manager
    manager.delete_table()

def test_persistence(dynamodb_manager):
    # Создать профиль
    profile1 = dynamodb_manager.get_profile("test_123")
    original_name = profile1.name
    
    # Изменить данные
    dynamodb_manager.change_seat("test_123", "OA476", "20A")
    dynamodb_manager.add_bag("test_123")
    
    # Создать новый manager (имитация перезапуска)
    manager2 = DynamoDBAirlineStateManager(
        region_name="us-east-1",
        table_prefix="test_airline",
        endpoint_url="http://localhost:8000"
    )
    
    # Данные должны сохраниться
    profile2 = manager2.get_profile("test_123")
    assert profile2.name == original_name
    assert profile2.bags_checked == 1
    segment = next(s for s in profile2.segments if s.flight_number == "OA476")
    assert segment.seat == "20A"
```

## 📊 Мониторинг и метрики

```python
from app.dynamodb import DynamoDBAirlineStateManager
import time

manager = DynamoDBAirlineStateManager(region_name="us-east-1")

# Замер производительности
start = time.time()

for i in range(100):
    profile = manager.get_profile(f"profile_{i}")
    manager.change_seat(f"profile_{i}", "OA476", "15A")

elapsed = time.time() - start
print(f"100 operations took {elapsed:.2f} seconds")
print(f"Average: {elapsed/100*1000:.2f} ms per operation")
```

## 🔧 Утилиты

### Массовое обновление

```python
def bulk_update_meal_preference(manager, profile_ids, meal):
    """Обновить предпочтение по еде для нескольких клиентов."""
    results = []
    for profile_id in profile_ids:
        try:
            result = manager.set_meal(profile_id, meal)
            results.append({"profile_id": profile_id, "success": True})
        except Exception as e:
            results.append({"profile_id": profile_id, "success": False, "error": str(e)})
    return results

# Использование
profile_ids = ["profile_1", "profile_2", "profile_3"]
results = bulk_update_meal_preference(manager, profile_ids, "vegetarian")
print(results)
```

### Экспорт данных

```python
def export_profiles(manager, output_file):
    """Экспортировать все профили в JSON."""
    import json
    
    # Получить все profile_ids (нужен отдельный механизм трекинга)
    # Для примера используем известные IDs
    profile_ids = ["profile_1", "profile_2", "profile_3"]
    
    profiles = {}
    for profile_id in profile_ids:
        profile = manager.get_profile(profile_id)
        profiles[profile_id] = profile.to_dict()
    
    with open(output_file, 'w') as f:
        json.dump(profiles, f, indent=2)
    
    print(f"Exported {len(profiles)} profiles to {output_file}")

# Использование
export_profiles(manager, "profiles_backup.json")
```

## 🎓 Best Practices

1. **Переиспользуйте manager instance** - не создавайте новый для каждой операции
2. **Используйте profile_id стабильно** - один клиент = один profile_id
3. **Обрабатывайте исключения** - `ValueError` для бизнес-логики, другие для инфраструктуры
4. **Логируйте timeline** - используется для аудита и отладки
5. **Тестируйте с локальным DynamoDB** - быстрее и дешевле
6. **Используйте connection pooling** - boto3 делает это автоматически
7. **Мониторьте метрики DynamoDB** - следите за RCU/WCU и throttling
