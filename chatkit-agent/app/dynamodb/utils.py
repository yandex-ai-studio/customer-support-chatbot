"""
Utility functions for working with DynamoDB.

Provides serialization and deserialization helpers for Python objects to ensure
compatibility with DynamoDB's type system.

Key functions:
- serialize_for_dynamodb: Converts Python objects to DynamoDB-compatible types
- deserialize_from_dynamodb: Converts DynamoDB objects back to Python types

These functions are used by:
- store.py: For storing ChatKit threads, messages, and attachments

Type conversions:
- float → Decimal (DynamoDB doesn't support float natively)
- datetime → ISO 8601 string
- set → list
- tuple → list
- Decimal → int/float (during deserialization)

Usage example:
    >>> from datetime import datetime
    >>> from dynamodb_utils import serialize_for_dynamodb, deserialize_from_dynamodb
    >>> 
    >>> data = {"price": 99.99, "timestamp": datetime.now()}
    >>> serialized = serialize_for_dynamodb(data)
    >>> # Now safe to store in DynamoDB
    >>> 
    >>> retrieved = deserialize_from_dynamodb(serialized)
    >>> # Back to native Python types
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any


def serialize_for_dynamodb(obj: Any) -> Any:
    """
    Конвертирует Python объекты для DynamoDB.
    
    DynamoDB имеет специфические требования к типам данных:
    - Не поддерживает float напрямую, нужно использовать Decimal
    - datetime нужно конвертировать в ISO 8601 строку
    - set конвертируется в list
    
    Args:
        obj: Объект Python для конвертации
        
    Returns:
        Объект, совместимый с DynamoDB
    """
    if obj is None:
        return None
    elif isinstance(obj, bool):
        # Bool должен быть проверен до int, т.к. bool является подклассом int
        return obj
    elif isinstance(obj, datetime):
        # Конвертируем datetime в ISO строку
        return obj.isoformat()
    elif isinstance(obj, float):
        # Конвертируем float в Decimal
        return Decimal(str(obj))
    elif isinstance(obj, int):
        # int поддерживается DynamoDB нативно
        return obj
    elif isinstance(obj, str):
        # string поддерживается DynamoDB нативно
        return obj
    elif isinstance(obj, bytes):
        # bytes поддерживается DynamoDB нативно
        return obj
    elif isinstance(obj, dict):
        # Рекурсивно обрабатываем словарь
        return {k: serialize_for_dynamodb(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        # Рекурсивно обрабатываем списки и кортежи
        return [serialize_for_dynamodb(v) for v in obj]
    elif isinstance(obj, set):
        # Множества конвертируем в списки
        return [serialize_for_dynamodb(v) for v in obj]
    else:
        # Для других типов пытаемся конвертировать в строку
        return str(obj)


def deserialize_from_dynamodb(obj: Any) -> Any:
    """
    Конвертирует DynamoDB объекты обратно в Python типы.
    
    Args:
        obj: Объект из DynamoDB
        
    Returns:
        Объект Python с нативными типами
    """
    if obj is None:
        return None
    elif isinstance(obj, Decimal):
        # Конвертируем Decimal в int или float
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    elif isinstance(obj, dict):
        # Рекурсивно обрабатываем словарь
        return {k: deserialize_from_dynamodb(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Рекурсивно обрабатываем список
        return [deserialize_from_dynamodb(v) for v in obj]
    else:
        # Остальные типы возвращаем как есть
        return obj
