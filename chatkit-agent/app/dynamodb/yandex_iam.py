"""
Yandex Cloud IAM authentication для Document API.

Автоматически получает IAM токен из metadata service и использует его
для авторизации запросов к YDB Document API.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

import requests

logger = logging.getLogger(__name__)


class YandexIAMTokenProvider:
    """
    Провайдер IAM токенов Yandex Cloud через metadata service.
    """

    METADATA_URL = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    TOKEN_REFRESH_MARGIN = timedelta(minutes=5)

    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: Optional[datetime] = None

    def get_token(self) -> str:
        """
        Получает актуальный IAM токен.
        Автоматически обновляет при необходимости.
        """
        if self._should_refresh():
            self._fetch_token()

        if not self._token:
            raise RuntimeError("Failed to obtain IAM token")

        return self._token

    def _should_refresh(self) -> bool:
        """Проверяет, нужно ли обновить токен."""
        if not self._token or not self._expires_at:
            return True

        # Обновляем токен за 5 минут до истечения
        return datetime.now() >= (self._expires_at - self.TOKEN_REFRESH_MARGIN)

    def _fetch_token(self) -> None:
        """Получает новый токен из metadata service."""
        try:
            logger.debug("Fetching IAM token from metadata service")

            response = requests.get(
                self.METADATA_URL,
                headers={"Metadata-Flavor": "Google"},
                timeout=5,
            )
            response.raise_for_status()

            data = response.json()
            self._token = data["access_token"]
            expires_in = int(data.get("expires_in", 3600))
            self._expires_at = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"IAM token obtained (expires in {expires_in}s)")

        except Exception as e:
            logger.error(f"Failed to fetch IAM token: {e}")
            raise RuntimeError(f"Cannot get IAM token from metadata service: {e}") from e

    def is_available(self) -> bool:
        """Проверяет доступность metadata service."""
        try:
            response = requests.get(
                self.METADATA_URL,
                headers={"Metadata-Flavor": "Google"},
                timeout=2,
            )
            return response.status_code == 200
        except Exception:
            return False


def is_yandex_cloud() -> bool:
    """
    Определяет, запущен ли код в Yandex Cloud.
    
    Returns:
        True если код выполняется в Yandex Cloud (Serverless Container, Function, VM)
    """
    # Проверяем переменные окружения
    if os.getenv("YANDEX_CLOUD_CONTAINER_ID"):
        return True

    # Проверяем доступность metadata service
    provider = YandexIAMTokenProvider()
    return provider.is_available()


def get_iam_token() -> str:
    """
    Получает IAM токен для текущего окружения.
    
    Returns:
        IAM токен
        
    Raises:
        RuntimeError: Если токен недоступен
    """
    provider = YandexIAMTokenProvider()
    return provider.get_token()


def get_yandex_boto_config():
    """
    Возвращает конфигурацию boto3 для Yandex Cloud.
    
    Отключает AWS Signature V4 (signature_version=UNSIGNED),
    так как Yandex Cloud Document API использует Bearer токены.
    
    Returns:
        botocore.config.Config для использования с boto3.client/resource
    """
    from botocore.config import Config
    from botocore import UNSIGNED

    return Config(signature_version=UNSIGNED)


def setup_yandex_auth(client):
    """
    Настраивает boto3 client для использования Yandex Cloud IAM токена.
    
    Добавляет Bearer токен авторизацию через event handler.
    AWS Signature должна быть отключена через Config(signature_version=UNSIGNED).
    
    Args:
        client: boto3 client или resource.meta.client
        
    Example:
        >>> from botocore import UNSIGNED
        >>> from botocore.config import Config
        >>> 
        >>> # При создании клиента
        >>> config = Config(signature_version=UNSIGNED)
        >>> dynamodb = boto3.resource('dynamodb', config=config, ...)
        >>> 
        >>> # Затем настраиваем IAM auth
        >>> setup_yandex_auth(dynamodb.meta.client)
    """
    if not is_yandex_cloud():
        logger.debug("Not in Yandex Cloud, skipping IAM auth setup")
        return

    logger.info("🔐 Setting up Yandex Cloud IAM authentication")

    # Создаём token provider
    token_provider = YandexIAMTokenProvider()

    def add_yandex_auth(event_name=None, **kwargs):
        """
        Event handler для добавления Bearer токена.
        Вызывается перед отправкой HTTP запроса.
        """
        request = kwargs.get('params')
        if request:
            # Получаем актуальный IAM токен
            iam_token = token_provider.get_token()

            # Устанавливаем Bearer токен авторизацию
            request['headers']['Authorization'] = f'Bearer {iam_token}'

    # Регистрируем на 'before-call' - перед отправкой HTTP запроса
    # AWS Signature уже НЕ создаётся благодаря signature_version=UNSIGNED
    client.meta.events.register('before-call', add_yandex_auth)

    logger.info("Yandex Cloud IAM auth configured")
