"""
DynamoDB integration module for Airline State Management.

Provides persistent storage for customer profiles and flight data using AWS DynamoDB
and compatible APIs (like Yandex Cloud Document API).

Main components:
- DynamoDBAirlineStateManager: Persistent storage for customer profiles and flight data
- serialize_for_dynamodb/deserialize_from_dynamodb: Type conversion utilities
- Yandex Cloud IAM integration utilities

Usage:
    from app.dynamodb import DynamoDBAirlineStateManager
    
    # Create airline state manager
    airline_state = DynamoDBAirlineStateManager(
        region_name="us-east-1",
        table_prefix="airline",
        endpoint_url="https://..."  # Optional, for non-AWS endpoints
    )
    
    # Create table
    airline_state.create_table()
    
    # Use the manager
    profile = airline_state.get_profile("profile_id")
"""

from .airline_state import DynamoDBAirlineStateManager
from .utils import deserialize_from_dynamodb, serialize_for_dynamodb
from .yandex_iam import get_yandex_boto_config, is_yandex_cloud, setup_yandex_auth

__all__ = [
    "DynamoDBAirlineStateManager",
    "serialize_for_dynamodb",
    "deserialize_from_dynamodb",
    "is_yandex_cloud",
    "setup_yandex_auth",
    "get_yandex_boto_config",
]
