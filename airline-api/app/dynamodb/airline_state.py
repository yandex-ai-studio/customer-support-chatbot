"""
DynamoDB-backed implementation of AirlineStateManager.
Stores customer profiles in DynamoDB for persistence across restarts.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

from ..airline_state import AirlineStateManager, CustomerProfile, FlightSegment
from .utils import (
    deserialize_from_dynamodb,
    serialize_for_dynamodb,
)
from .yandex_iam import setup_yandex_auth

logger = logging.getLogger(__name__)

class DynamoDBAirlineStateManager(AirlineStateManager):
    """
    DynamoDB-backed implementation of AirlineStateManager.
    Stores customer profiles in a dedicated DynamoDB table.
    """

    def __init__(
            self,
            region_name: str | None = None,
            endpoint_url: str | None = None,
            table_prefix: str = "airline",
    ):
        """
        Инициализирует DynamoDB state manager.

        Args:
            region_name: AWS регион (по умолчанию из env AWS_REGION)
            endpoint_url: Кастомный endpoint для совместимых API (например, Yandex Cloud)
            table_prefix: Префикс для имён таблиц
        """
        # Не вызываем super().__init__() т.к. не нужен словарь в памяти

        self.region_name = region_name or os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = endpoint_url
        self.table_prefix = table_prefix

        # Создаём клиента и ресурс DynamoDB
        from .yandex_iam import get_yandex_boto_config, is_yandex_cloud

        dynamodb_kwargs = {"region_name": self.region_name}
        if self.endpoint_url:
            dynamodb_kwargs["endpoint_url"] = self.endpoint_url

        if is_yandex_cloud():
            # Отключаем AWS Signature V4 для Yandex Cloud
            dynamodb_kwargs["config"] = get_yandex_boto_config()

        self.dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)
        self.dynamodb_client = boto3.client("dynamodb", **dynamodb_kwargs)

        # Настраиваем Yandex Cloud IAM auth (если запущено в Yandex Cloud)
        setup_yandex_auth(self.dynamodb.meta.client)
        setup_yandex_auth(self.dynamodb_client)

        # Имя таблицы для профилей клиентов
        self.profiles_table_name = f"{self.table_prefix}_profiles"
        self.profiles_table = self.dynamodb.Table(self.profiles_table_name)

    def create_table(self) -> None:
        """
        Создаёт таблицу для хранения профилей клиентов.
        
        Схема таблицы:
        - Primary Key: profile_id (String)
        - Attributes: data (Map) - сериализованный CustomerProfile
        """
        try:
            self.dynamodb_client.create_table(
                TableName=self.profiles_table_name,
                KeySchema=[
                    {"AttributeName": "profile_id", "KeyType": "HASH"},
                ],
                AttributeDefinitions=[
                    {"AttributeName": "profile_id", "AttributeType": "S"},
                ],
                BillingMode="PAY_PER_REQUEST",  # On-demand pricing
            )

            # Ждём создания таблицы
            waiter = self.dynamodb_client.get_waiter("table_exists")
            waiter.wait(TableName=self.profiles_table_name)

            logger.debug(f"Created table: {self.profiles_table_name}")

        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceInUseException":
                logger.debug(f"Table {self.profiles_table_name} already exists")
            else:
                raise

    def delete_table(self) -> None:
        """Удаляет таблицу профилей."""
        try:
            self.dynamodb_client.delete_table(TableName=self.profiles_table_name)
            logger.debug(f"Deleted table: {self.profiles_table_name}")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                logger.debug(f"Table {self.profiles_table_name} does not exist")
            else:
                raise

    def table_exists(self) -> bool:
        """Проверяет, существует ли таблица."""
        try:
            self.dynamodb_client.describe_table(TableName=self.profiles_table_name)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                return False
            raise

    def get_profile(self, profile_id: str) -> CustomerProfile:
        """
        Получает профиль клиента из DynamoDB.
        Если профиль не найден, создаётся дефолтный и сохраняется.
        """
        try:
            response = self.profiles_table.get_item(Key={"profile_id": profile_id})

            if "Item" in response:
                # Десериализуем данные из DynamoDB
                data = deserialize_from_dynamodb(response["Item"]["data"])

                # Восстанавливаем FlightSegment объекты
                segments = [FlightSegment(**seg) for seg in data["segments"]]
                data["segments"] = segments

                # Создаём CustomerProfile
                return CustomerProfile(**data)
            else:
                # Профиль не найден - создаём дефолтный
                profile = self._create_default_state(profile_id)
                self._save_profile(profile_id, profile)
                return profile

        except Exception as e:
            logger.debug(f"Error loading profile for {profile_id}: {e}")
            # В случае ошибки создаём дефолтный профиль
            profile = self._create_default_state(profile_id)
            self._save_profile(profile_id, profile)
            return profile

    def _save_profile(self, profile_id: str, profile: CustomerProfile) -> None:
        """Сохраняет профиль клиента в DynamoDB."""
        # Конвертируем профиль в словарь
        data = profile.to_dict()

        # Сериализуем для DynamoDB
        serialized_data = serialize_for_dynamodb(data)

        # Создаём item
        item = {
            "profile_id": profile_id,
            "data": serialized_data,
        }

        # Сериализуем весь item
        item = serialize_for_dynamodb(item)

        # Сохраняем в DynamoDB
        self.profiles_table.put_item(Item=item)

    def change_seat(self, profile_id: str, flight_number: str, seat: str) -> str:
        profile = self.get_profile(profile_id)
        if not self._is_valid_seat(seat):
            raise ValueError("Seat must be a row number followed by a letter, for example 12C.")

        segment = self._find_segment(profile, flight_number)
        if segment is None:
            raise ValueError(f"Flight {flight_number} is not on the customer's itinerary.")

        previous = segment.seat
        segment.change_seat(seat.upper())
        profile.log(
            f"Seat changed on {segment.flight_number} from {previous} to {segment.seat}.",
            kind="success",
        )

        self._save_profile(profile_id, profile)

        return f"Seat updated to {segment.seat} on flight {segment.flight_number}."

    def cancel_trip(self, profile_id: str) -> str:
        """Отменяет поездку и сохраняет в DynamoDB."""
        profile = self.get_profile(profile_id)
        for segment in profile.segments:
            segment.cancel()
        profile.log("Trip cancelled at customer request.", kind="warning")
        self._save_profile(profile_id, profile)
        return "The reservation has been cancelled. Refund processing will begin immediately."

    def add_bag(self, profile_id: str) -> str:
        """Добавляет багаж и сохраняет в DynamoDB."""
        profile = self.get_profile(profile_id)
        profile.bags_checked += 1
        profile.log(f"Added checked bag. Total bags now {profile.bags_checked}.", kind="info")
        self._save_profile(profile_id, profile)
        return f"Checked bag added. You now have {profile.bags_checked} bag(s) checked."

    def set_meal(self, profile_id: str, meal: str) -> str:
        """Устанавливает предпочтение по еде и сохраняет в DynamoDB."""
        profile = self.get_profile(profile_id)
        profile.meal_preference = meal
        profile.log(f"Meal preference updated to {meal}.", kind="info")
        self._save_profile(profile_id, profile)
        return f"We'll note {meal} as the meal preference."

    def request_assistance(self, profile_id: str, note: str) -> str:
        """Запрашивает помощь и сохраняет в DynamoDB."""
        profile = self.get_profile(profile_id)
        profile.special_assistance = note
        profile.log(f"Special assistance noted: {note}.", kind="info")
        self._save_profile(profile_id, profile)
        return "Assistance request recorded. Airport staff will be notified."

    def get_profile_dict(self, profile_id: str) -> Dict[str, Any]:
        """Возвращает профиль в виде словаря."""
        return self.get_profile(profile_id).to_dict()
