#!/usr/bin/env python3
"""
DynamoDB management script for ChatKit store.

Usage:
    python -m app.dynamodb.manage_dynamodb --create          # Create tables
    python -m app.dynamodb.manage_dynamodb --delete          # Delete tables
    python -m app.dynamodb.manage_dynamodb --status          # Check table status
    python -m app.dynamodb.manage_dynamodb --stats           # Show table statistics
    python -m app.dynamodb.manage_dynamodb --list-threads    # List all threads
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.dynamodb import DynamoDBStore

logger = logging.getLogger(__name__)


def create_tables(store: DynamoDBStore):
    """Create DynamoDB tables."""
    logger.debug("\n📦 Creating DynamoDB tables...")
    store.create_tables()
    logger.debug("✅ All tables created successfully!\n")


def delete_tables(store: DynamoDBStore):
    """Delete DynamoDB tables."""
    logger.debug("\n⚠️  WARNING: This will DELETE ALL DATA!")
    response = input("Type 'yes' to confirm: ")

    if response.lower() != "yes":
        logger.debug("❌ Aborted")
        return

    dynamodb_client = boto3.client(
        "dynamodb",
        region_name=store.region_name,
        endpoint_url=store.endpoint_url,
    )

    tables = [
        store.threads_table_name,
        store.items_table_name,
        store.attachments_table_name,
    ]

    for table_name in tables:
        try:
            logger.debug(f"🗑️  Deleting table: {table_name}")
            dynamodb_client.delete_table(TableName=table_name)
            logger.debug(f"✅ Deleted: {table_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.debug(f"ℹ️  Table doesn't exist: {table_name}")
            else:
                logger.debug(f"❌ Error deleting {table_name}: {e}")

    logger.debug("\n✅ All tables deleted!\n")


def check_status(store: DynamoDBStore):
    """Check status of DynamoDB tables."""
    dynamodb_client = boto3.client(
        "dynamodb",
        region_name=store.region_name,
        endpoint_url=store.endpoint_url,
    )

    tables = {
        "Threads": store.threads_table_name,
        "Thread Items": store.items_table_name,
        "Attachments": store.attachments_table_name,
    }

    logger.debug("\n📊 Table Status:\n")

    for display_name, table_name in tables.items():
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            table = response["Table"]
            status = table["TableStatus"]
            item_count = table["ItemCount"]

            status_emoji = "✅" if status == "ACTIVE" else "⏳"
            logger.debug(f"{status_emoji} {display_name}: {status}")
            logger.debug(f"   Table name: {table_name}")
            logger.debug(f"   Items: {item_count}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.debug(f"❌ {display_name}: NOT FOUND")
                logger.debug(f"   Table name: {table_name}")
            else:
                logger.debug(f"❌ Error checking {display_name}: {e}\n")


def show_stats(store: DynamoDBStore):
    """Show statistics for DynamoDB tables."""
    dynamodb_client = boto3.client(
        "dynamodb",
        region_name=store.region_name,
        endpoint_url=store.endpoint_url,
    )

    tables = {
        "Threads": store.threads_table_name,
        "Thread Items": store.items_table_name,
        "Attachments": store.attachments_table_name,
    }

    logger.debug("\n📈 Table Statistics:\n")

    total_size = 0

    for display_name, table_name in tables.items():
        try:
            response = dynamodb_client.describe_table(TableName=table_name)
            table = response["Table"]

            item_count = table["ItemCount"]
            size_bytes = table["TableSizeBytes"]
            size_mb = size_bytes / (1024 * 1024)

            total_size += size_bytes

            logger.debug(f"📊 {display_name}:")
            logger.debug(f"   Items: {item_count:,}")
            logger.debug(f"   Size: {size_mb:.2f} MB")
            logger.debug(f"   Billing: {table.get('BillingModeSummary', {}).get('BillingMode', 'N/A')}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.debug(f"❌ {display_name}: NOT FOUND\n")
            else:
                logger.debug(f"❌ Error getting stats for {display_name}: {e}\n")

    total_size_mb = total_size / (1024 * 1024)
    logger.debug(f"📦 Total size: {total_size_mb:.2f} MB\n")


def list_threads(store: DynamoDBStore):
    """List all threads."""
    logger.debug("\n🧵 Threads:\n")

    try:
        response = store.threads_table.scan(Limit=20)
        items = response.get("Items", [])

        if not items:
            logger.debug("  No threads found.")
            return

        for item in items:
            thread_id = item.get("id", "unknown")
            created_at = item.get("created_at", "unknown")
            logger.debug(f"  • Thread ID: {thread_id}")
            logger.debug(f"    Created: {created_at}")

        if response.get("LastEvaluatedKey"):
            logger.debug("  ... (showing first 20 threads)")

    except Exception as e:
        logger.debug(f"❌ Error listing threads: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage DynamoDB tables for ChatKit store"
    )
    parser.add_argument("--create", action="store_true", help="Create tables")
    parser.add_argument("--delete", action="store_true", help="Delete tables")
    parser.add_argument("--status", action="store_true", help="Check table status")
    parser.add_argument("--stats", action="store_true", help="Show table statistics")
    parser.add_argument(
        "--list-threads", action="store_true", help="List all threads"
    )
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    parser.add_argument("--prefix", default="chatkit", help="Table prefix")
    parser.add_argument(
        "--endpoint-url", default=None, help="Endpoint URL for local DynamoDB"
    )

    args = parser.parse_args()

    # Use environment variables if available
    region = os.environ.get("AWS_REGION", args.region)
    prefix = os.environ.get("DYNAMODB_TABLE_PREFIX", args.prefix)
    endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL", args.endpoint_url)

    logger.debug(f"Region: {region}")
    logger.debug(f"Table prefix: {prefix}")
    if endpoint_url:
        logger.debug(f"Endpoint URL: {endpoint_url}")

    store = DynamoDBStore(
        region_name=region,
        table_prefix=prefix,
        endpoint_url=endpoint_url,
    )

    if args.create:
        create_tables(store)
    elif args.delete:
        delete_tables(store)
    elif args.status:
        check_status(store)
    elif args.stats:
        show_stats(store)
    elif args.list_threads:
        list_threads(store)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
