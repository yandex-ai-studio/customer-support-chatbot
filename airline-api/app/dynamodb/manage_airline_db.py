#!/usr/bin/env python3
"""
Airline DynamoDB management script.

Управление DynamoDB таблицей для профилей клиентов авиакомпании.

Usage:
    python -m app.dynamodb.manage_airline_db --create    # Создать таблицу
    python -m app.dynamodb.manage_airline_db --delete    # Удалить таблицу
    python -m app.dynamodb.manage_airline_db --status    # Статус таблицы
    python -m app.dynamodb.manage_airline_db --list      # Список профилей
    python -m app.dynamodb.manage_airline_db --stats     # Статистика
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime

from botocore.exceptions import ClientError

from .airline_state import DynamoDBAirlineStateManager


def get_manager() -> DynamoDBAirlineStateManager:
    """Создаёт airline state manager из переменных окружения."""
    region = os.environ.get("AWS_REGION", "us-east-1")
    table_prefix = os.environ.get("DYNAMODB_TABLE_PREFIX", "airline")
    endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")

    return DynamoDBAirlineStateManager(
        region_name=region,
        table_prefix=table_prefix,
        endpoint_url=endpoint_url,
    )


def create_table():
    """Создать таблицу для профилей."""
    print("📦 Creating DynamoDB table for airline profiles...")
    manager = get_manager()
    manager.create_table()
    print("✅ Table created successfully!")


def delete_table():
    """Удалить таблицу профилей."""
    print("\n⚠️  WARNING: This will DELETE ALL customer profile data!")
    response = input("Type 'yes' to confirm: ")

    if response.lower() != "yes":
        print("❌ Aborted")
        return

    print("🗑️  Deleting table...")
    manager = get_manager()
    manager.delete_table()
    print("✅ Table deleted")


def show_status():
    """Показать статус таблицы."""
    manager = get_manager()

    if not manager.table_exists():
        print(f"❌ Table {manager.profiles_table_name} does not exist")
        return

    try:
        response = manager.dynamodb_client.describe_table(
            TableName=manager.profiles_table_name
        )
        table = response["Table"]

        print(f"\n✅ Table: {table['TableName']}")
        print(f"   Status: {table['TableStatus']}")
        print(f"   Created: {datetime.fromtimestamp(table['CreationDateTime'].timestamp())}")
        print(f"   Item count: {table['ItemCount']}")
        print(f"   Size: {table['TableSizeBytes'] / 1024:.2f} KB")
        print(f"   Billing mode: {table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')}")

    except ClientError as e:
        print(f"❌ Error: {e}")


def list_profiles():
    """Список всех профилей клиентов."""
    manager = get_manager()

    if not manager.table_exists():
        print(f"❌ Table {manager.profiles_table_name} does not exist")
        return

    print(f"\n📋 Customer Profiles in {manager.profiles_table_name}:\n")

    try:
        response = manager.profiles_table.scan()
        items = response.get("Items", [])

        if not items:
            print("   (no profiles found)")
            return

        for item in items:
            profile_id = item.get("profile_id", "unknown")
            data = item.get("data", {})

            print(f"   Profile ID: {profile_id}")
            if isinstance(data, dict):
                name = data.get("name", "N/A")
                customer_id = data.get("customer_id", "N/A")
                loyalty_status = data.get("loyalty_status", "N/A")
                bags = data.get("bags_checked", 0)
                segments_count = len(data.get("segments", []))

                print(f"      Name: {name}")
                print(f"      Customer ID: {customer_id}")
                print(f"      Loyalty: {loyalty_status}")
                print(f"      Bags: {bags}")
                print(f"      Segments: {segments_count}")
            print()

        print(f"   Total: {len(items)} profile(s)")

    except ClientError as e:
        print(f"❌ Error: {e}")


def show_stats():
    """Показать статистику таблицы."""
    manager = get_manager()

    if not manager.table_exists():
        print(f"❌ Table {manager.profiles_table_name} does not exist")
        return

    try:
        response = manager.dynamodb_client.describe_table(
            TableName=manager.profiles_table_name
        )
        table = response["Table"]

        print(f"\n📊 Statistics for {table['TableName']}:")
        print(f"   Items: {table['ItemCount']}")
        print(f"   Size: {table['TableSizeBytes'] / 1024:.2f} KB")
        print(f"   ARN: {table['TableArn']}")

        # Scan для детальной статистики
        scan_response = manager.profiles_table.scan()
        items = scan_response.get("Items", [])

        total_bags = 0
        total_segments = 0
        loyalty_statuses = {}

        for item in items:
            data = item.get("data", {})
            if isinstance(data, dict):
                total_bags += data.get("bags_checked", 0)
                segments = data.get("segments", [])
                total_segments += len(segments)

                status = data.get("loyalty_status", "Unknown")
                loyalty_statuses[status] = loyalty_statuses.get(status, 0) + 1

        print(f"\n   Customer Statistics:")
        print(f"      Total customers: {len(items)}")
        print(f"      Total bags: {total_bags}")
        print(f"      Total flight segments: {total_segments}")

        if loyalty_statuses:
            print(f"\n   Loyalty Status Distribution:")
            for status, count in loyalty_statuses.items():
                print(f"      {status}: {count}")

    except ClientError as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Manage DynamoDB table for airline customer profiles"
    )
    parser.add_argument("--create", action="store_true", help="Create table")
    parser.add_argument("--delete", action="store_true", help="Delete table")
    parser.add_argument("--status", action="store_true", help="Show table status")
    parser.add_argument("--list", action="store_true", help="List all profiles")
    parser.add_argument("--stats", action="store_true", help="Show statistics")

    args = parser.parse_args()

    if args.create:
        create_table()
    elif args.delete:
        delete_table()
    elif args.status:
        show_status()
    elif args.list:
        list_profiles()
    elif args.stats:
        show_stats()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
