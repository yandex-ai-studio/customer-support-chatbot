from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from pydantic import TypeAdapter
from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, Thread, ThreadItem, ThreadMetadata

from .utils import (
    deserialize_from_dynamodb as _deserialize_from_dynamodb,
    serialize_for_dynamodb as _serialize_for_dynamodb,
)
from .yandex_iam import setup_yandex_auth

# ThreadItem is a discriminated union, create TypeAdapter once for performance
_thread_item_adapter = TypeAdapter(ThreadItem)

logger = logging.getLogger(__name__)


class DynamoDBStore(Store[dict[str, Any]]):
    """
    AWS DynamoDB-based store implementation for ChatKit.
    
    Follows ChatKit recommendations to serialize models as JSON documents
    to handle model schema changes between library versions.
    
    Uses three DynamoDB tables:
    - chatkit_threads: Stores thread metadata
    - chatkit_thread_items: Stores messages, tool calls, etc.
    - chatkit_attachments: Stores attachment metadata
    
    Table schemas:
    
    chatkit_threads:
        PK: id (string)
        Attributes: data (map), created_at (number), updated_at (number)
    
    chatkit_thread_items:
        PK: thread_id (string)
        SK: item_id (string)
        Attributes: data (map), created_at (number), item_type (string)
        GSI: item_id-index (for loading by item_id)
        GSI: thread-created-index (for sorting items within thread by created_at)
    
    chatkit_attachments:
        PK: id (string)
        Attributes: data (map), created_at (number)
    """

    def __init__(
            self,
            region_name: str = "us-east-1",
            table_prefix: str = "chatkit",
            endpoint_url: str | None = None,
    ) -> None:
        """
        Initialize the DynamoDB store.
        
        Args:
            region_name: AWS region name (default: us-east-1)
            table_prefix: Prefix for table names (default: chatkit)
            endpoint_url: Optional endpoint URL (for local DynamoDB)
        """
        self.region_name = region_name
        self.table_prefix = table_prefix
        self.endpoint_url = endpoint_url

        # Initialize DynamoDB resource
        # Для Yandex Cloud отключаем AWS Signature и используем IAM токен
        from .yandex_iam import get_yandex_boto_config, is_yandex_cloud

        dynamodb_kwargs = {
            "region_name": region_name,
            "endpoint_url": endpoint_url,
        }

        if is_yandex_cloud():
            # Отключаем AWS Signature V4 (используем Bearer токен вместо него)
            dynamodb_kwargs["config"] = get_yandex_boto_config()

        self.dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)

        # Настраиваем Yandex Cloud IAM auth (если запущено в Yandex Cloud)
        setup_yandex_auth(self.dynamodb.meta.client)

        # Table names
        self.threads_table_name = f"{table_prefix}_threads"
        self.items_table_name = f"{table_prefix}_thread_items"
        self.attachments_table_name = f"{table_prefix}_attachments"

        # Table references
        self.threads_table = self.dynamodb.Table(self.threads_table_name)
        self.items_table = self.dynamodb.Table(self.items_table_name)
        self.attachments_table = self.dynamodb.Table(self.attachments_table_name)

    def create_tables(self) -> None:
        """
        Create DynamoDB tables if they don't exist.
        Should be called once during setup.
        """
        from .yandex_iam import get_yandex_boto_config, is_yandex_cloud

        client_kwargs = {
            "region_name": self.region_name,
            "endpoint_url": self.endpoint_url,
        }

        if is_yandex_cloud():
            # Отключаем AWS Signature V4 для Yandex Cloud
            client_kwargs["config"] = get_yandex_boto_config()

        dynamodb_client = boto3.client("dynamodb", **client_kwargs)

        # Настраиваем Yandex Cloud IAM auth для client
        setup_yandex_auth(dynamodb_client)

        # Create threads table
        try:
            dynamodb_client.create_table(
                TableName=self.threads_table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "N"},
                    {"AttributeName": "updated_at", "AttributeType": "N"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "created_at-index",
                        "KeySchema": [
                            {"AttributeName": "id", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                    {
                        "IndexName": "updated_at-index",
                        "KeySchema": [
                            {"AttributeName": "id", "KeyType": "HASH"},
                            {"AttributeName": "updated_at", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    }
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            logger.debug(f"Created table: {self.threads_table_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceInUseException":
                raise
            logger.debug(f"Table already exists: {self.threads_table_name}")

        # Create thread items table
        # Note: Using GSI instead of LSI for compatibility with Yandex Cloud Document API
        try:
            dynamodb_client.create_table(
                TableName=self.items_table_name,
                KeySchema=[
                    {"AttributeName": "thread_id", "KeyType": "HASH"},
                    {"AttributeName": "item_id", "KeyType": "RANGE"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "thread_id", "AttributeType": "S"},
                    {"AttributeName": "item_id", "AttributeType": "S"},
                    {"AttributeName": "created_at", "AttributeType": "N"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "item_id-index",
                        "KeySchema": [
                            {"AttributeName": "item_id", "KeyType": "HASH"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                    {
                        "IndexName": "thread-created-index",
                        "KeySchema": [
                            {"AttributeName": "thread_id", "KeyType": "HASH"},
                            {"AttributeName": "created_at", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    }
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            logger.debug(f"Created table: {self.items_table_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceInUseException":
                raise
            logger.debug(f"Table already exists: {self.items_table_name}")

        # Create attachments table
        try:
            dynamodb_client.create_table(
                TableName=self.attachments_table_name,
                KeySchema=[
                    {"AttributeName": "id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "id", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5,
                },
            )
            logger.debug(f"Created table: {self.attachments_table_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceInUseException":
                raise
            logger.debug(f"Table already exists: {self.attachments_table_name}")

        # Wait for tables to be active
        logger.debug("Waiting for tables to be active...")
        for table_name in [
            self.threads_table_name,
            self.items_table_name,
            self.attachments_table_name,
        ]:
            waiter = dynamodb_client.get_waiter("table_exists")
            waiter.wait(TableName=table_name)

        logger.debug("All tables are ready!")

    @staticmethod
    def _coerce_thread_metadata(thread: ThreadMetadata | Thread) -> ThreadMetadata:
        """
        Return thread metadata without any embedded items (openai-chatkit>=1.0).
        
        This ensures we only store metadata in the threads table,
        not the full thread with items.
        """
        has_items = isinstance(thread, Thread) or "items" in getattr(
            thread, "model_fields_set", set()
        )
        if not has_items:
            return thread.model_copy(deep=True)

        data = thread.model_dump()
        data.pop("items", None)
        return ThreadMetadata(**data).model_copy(deep=True)

    @staticmethod
    def _datetime_to_timestamp(dt: datetime | None) -> float:
        """Convert datetime to Unix timestamp."""
        if dt is None:
            dt = datetime.now()
        return dt.timestamp()

    @staticmethod
    def _timestamp_to_datetime(ts: float | Decimal) -> datetime:
        """Convert Unix timestamp to datetime."""
        return datetime.fromtimestamp(float(ts))

    # -- Thread metadata methods -------------------------------------------------

    async def load_thread(
            self, thread_id: str, context: dict[str, Any]
    ) -> ThreadMetadata:
        """Load thread metadata by ID."""
        try:
            response = self.threads_table.get_item(Key={"id": thread_id})

            if "Item" not in response:
                raise NotFoundError(f"Thread {thread_id} not found")

            item = response["Item"]
            thread_data = _deserialize_from_dynamodb(item["data"])
            return ThreadMetadata(**thread_data)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise NotFoundError(f"Thread {thread_id} not found")
            raise

    async def save_thread(
            self, thread: ThreadMetadata, context: dict[str, Any]
    ) -> None:
        """Save or update thread metadata."""
        metadata = self._coerce_thread_metadata(thread)
        thread_dict = metadata.model_dump()

        item = {
            "id": metadata.id,
            "data": thread_dict,
            "created_at": self._datetime_to_timestamp(metadata.created_at),
            "updated_at": self._datetime_to_timestamp(datetime.now()),
        }

        # Сериализуем весь item для DynamoDB
        serialized_item = _serialize_for_dynamodb(item)
        self.threads_table.put_item(Item=serialized_item)

    async def load_threads(
            self,
            limit: int,
            after: str | None,
            order: str,
            context: dict[str, Any],
    ) -> Page[ThreadMetadata]:
        """
        Load paginated list of threads.
        
        Note: DynamoDB pagination works differently than SQL.
        We scan all items and sort in memory for simplicity.
        For large datasets, consider using DynamoDB Streams or a separate index.
        """
        scan_kwargs = {}
        if after:
            # Get the created_at timestamp of the cursor thread
            try:
                cursor_thread = await self.load_thread(after, context)
                cursor_ts = self._datetime_to_timestamp(cursor_thread.created_at)

                if order == "desc":
                    scan_kwargs["FilterExpression"] = Key("created_at").lt(cursor_ts)
                else:
                    scan_kwargs["FilterExpression"] = Key("created_at").gt(cursor_ts)
            except NotFoundError:
                pass  # Cursor not found, start from beginning

        # Scan all threads (for production, use a GSI with pagination)
        response = self.threads_table.scan(**scan_kwargs)
        items = response.get("Items", [])

        # Handle pagination for large result sets
        while "LastEvaluatedKey" in response:
            response = self.threads_table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"],
                **scan_kwargs,
            )
            items.extend(response.get("Items", []))

        # Convert to ThreadMetadata objects
        threads = []
        for item in items:
            thread_data = _deserialize_from_dynamodb(item["data"])
            threads.append(ThreadMetadata(**thread_data))

        # Sort by created_at
        threads.sort(
            key=lambda t: t.created_at or datetime.min,
            reverse=(order == "desc"),
        )

        # Apply limit and check for more
        has_more = len(threads) > limit
        threads = threads[:limit]
        next_after = threads[-1].id if has_more and threads else None

        return Page(
            data=threads,
            has_more=has_more,
            after=next_after,
        )

    async def delete_thread(self, thread_id: str, context: dict[str, Any]) -> None:
        """Delete a thread and all its items."""
        # Delete thread metadata
        self.threads_table.delete_item(Key={"id": thread_id})

        # Delete all thread items
        response = self.items_table.query(
            KeyConditionExpression=Key("thread_id").eq(thread_id)
        )

        items = response.get("Items", [])

        # Handle pagination
        while "LastEvaluatedKey" in response:
            response = self.items_table.query(
                KeyConditionExpression=Key("thread_id").eq(thread_id),
                ExclusiveStartKey=response["LastEvaluatedKey"],
            )
            items.extend(response.get("Items", []))

        # Batch delete items
        with self.items_table.batch_writer() as batch:
            for item in items:
                batch.delete_item(
                    Key={"thread_id": item["thread_id"], "item_id": item["item_id"]}
                )

    # -- Thread items methods ----------------------------------------------------

    async def load_thread_items(
            self,
            thread_id: str,
            after: str | None,
            limit: int,
            order: str,
            context: dict[str, Any],
    ) -> Page[ThreadItem]:
        """Load paginated list of items in a thread."""
        query_kwargs = {
            "KeyConditionExpression": Key("thread_id").eq(thread_id),
            "IndexName": "thread-created-index",
            "ScanIndexForward": (order == "asc"),
            "Limit": limit + 1,  # Get one extra to check if there are more
        }

        if after:
            # Get the created_at timestamp of the cursor item
            try:
                cursor_item = await self.load_item(thread_id, after, context)
                cursor_ts = self._datetime_to_timestamp(
                    getattr(cursor_item, "created_at", None)
                )

                # DynamoDB doesn't support > or < in KeyConditionExpression easily
                # So we'll fetch and filter in memory for simplicity
                query_kwargs.pop("Limit")
            except NotFoundError:
                pass

        response = self.items_table.query(**query_kwargs)
        items_data = response.get("Items", [])

        # Handle pagination if no cursor
        if not after and "LastEvaluatedKey" in response and len(items_data) <= limit:
            response = self.items_table.query(
                ExclusiveStartKey=response["LastEvaluatedKey"],
                **query_kwargs,
            )
            items_data.extend(response.get("Items", []))

        # Convert to ThreadItem objects
        # ThreadItem is a discriminated union, use TypeAdapter for validation
        items = []
        for item_data in items_data:
            deserialized = _deserialize_from_dynamodb(item_data["data"])
            items.append(_thread_item_adapter.validate_python(deserialized))

        # Filter by cursor if needed
        if after:
            try:
                cursor_item = await self.load_item(thread_id, after, context)
                cursor_ts = self._datetime_to_timestamp(
                    getattr(cursor_item, "created_at", None)
                )

                if order == "desc":
                    items = [
                        item
                        for item in items
                        if self._datetime_to_timestamp(
                            getattr(item, "created_at", None)
                        )
                           < cursor_ts
                    ]
                else:
                    items = [
                        item
                        for item in items
                        if self._datetime_to_timestamp(
                            getattr(item, "created_at", None)
                        )
                           > cursor_ts
                    ]
            except NotFoundError:
                pass

        # Check for more and trim to limit
        has_more = len(items) > limit
        items = items[:limit]
        next_after = items[-1].id if has_more and items else None

        return Page(
            data=items,
            has_more=has_more,
            after=next_after,
        )

    async def add_thread_item(
            self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        """Add a new item to a thread."""
        item_dict = item.model_dump()

        dynamodb_item = {
            "thread_id": thread_id,
            "item_id": item.id,
            "data": item_dict,
            "created_at": self._datetime_to_timestamp(
                getattr(item, "created_at", None)
            ),
            "item_type": item_dict.get("type", "unknown"),
        }

        # Сериализуем весь item для DynamoDB
        serialized_item = _serialize_for_dynamodb(dynamodb_item)
        self.items_table.put_item(Item=serialized_item)

    async def save_item(
            self, thread_id: str, item: ThreadItem, context: dict[str, Any]
    ) -> None:
        """Save or update an item in a thread."""
        await self.add_thread_item(thread_id, item, context)

    async def load_item(
            self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> ThreadItem:
        """Load a specific item from a thread."""
        try:
            response = self.items_table.get_item(
                Key={"thread_id": thread_id, "item_id": item_id}
            )

            if "Item" not in response:
                raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")

            item_data = _deserialize_from_dynamodb(response["Item"]["data"])
            # ThreadItem is a discriminated union, use TypeAdapter
            from pydantic import TypeAdapter
            thread_item_adapter = TypeAdapter(ThreadItem)
            return thread_item_adapter.validate_python(item_data)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")
            raise

    async def delete_thread_item(
            self, thread_id: str, item_id: str, context: dict[str, Any]
    ) -> None:
        """Delete an item from a thread."""
        self.items_table.delete_item(
            Key={"thread_id": thread_id, "item_id": item_id}
        )

    # -- Attachment methods ------------------------------------------------------

    async def save_attachment(
            self,
            attachment: Attachment,
            context: dict[str, Any],
    ) -> None:
        """
        Save attachment metadata.
        
        Note: This only saves metadata. File bytes should be stored separately
        in S3 or another blob storage service.
        """
        attachment_dict = attachment.model_dump()

        item = {
            "id": attachment.id,
            "data": attachment_dict,
            "created_at": self._datetime_to_timestamp(datetime.now()),
        }

        # Сериализуем весь item для DynamoDB
        serialized_item = _serialize_for_dynamodb(item)
        self.attachments_table.put_item(Item=serialized_item)

    async def load_attachment(
            self,
            attachment_id: str,
            context: dict[str, Any],
    ) -> Attachment:
        """Load attachment metadata by ID."""
        try:
            response = self.attachments_table.get_item(Key={"id": attachment_id})

            if "Item" not in response:
                raise NotFoundError(f"Attachment {attachment_id} not found")

            attachment_data = _deserialize_from_dynamodb(response["Item"]["data"])
            return Attachment(**attachment_data)

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                raise NotFoundError(f"Attachment {attachment_id} not found")
            raise

    async def delete_attachment(
            self, attachment_id: str, context: dict[str, Any]
    ) -> None:
        """
        Delete attachment metadata.
        
        Note: This only deletes metadata. File bytes should be deleted separately
        from your blob storage service (S3).
        """
        self.attachments_table.delete_item(Key={"id": attachment_id})
