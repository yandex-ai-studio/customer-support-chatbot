"""
DynamoDB integration module.

Provides store implementations and utilities for working with AWS DynamoDB
and compatible APIs (like Yandex Cloud Document API).

Main components:
- DynamoDBStore: ChatKit store implementation for threads, messages, and attachments
- serialize_for_dynamodb/deserialize_from_dynamodb: Type conversion utilities
- Yandex Cloud IAM integration utilities

Usage:
    from app.dynamodb import DynamoDBStore
    
    # Create store
    store = DynamoDBStore(
        region_name="us-east-1",
        table_prefix="chatkit",
        endpoint_url="https://..."  # Optional, for non-AWS endpoints
    )
    
    # Create tables
    store.create_tables()
"""

from .store import DynamoDBStore
from .utils import deserialize_from_dynamodb, serialize_for_dynamodb
from .yandex_iam import get_yandex_boto_config, is_yandex_cloud, setup_yandex_auth

__all__ = [
    "DynamoDBStore",
    "serialize_for_dynamodb",
    "deserialize_from_dynamodb",
    "is_yandex_cloud",
    "setup_yandex_auth",
    "get_yandex_boto_config",
]

