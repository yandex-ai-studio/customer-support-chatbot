"""
Airline REST API Service
Независимый микросервис для управления профилями клиентов авиакомпании
"""
from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .airline_state import AirlineStateManager
from .dynamodb import DynamoDBAirlineStateManager

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Airline API",
    description="REST API для управления профилями клиентов авиакомпании",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# Pydantic модели для запросов
class ChangeSeatRequest(BaseModel):
    profile_id: str
    flight_number: str
    seat: str


class CancelTripRequest(BaseModel):
    profile_id: str


class AddBagRequest(BaseModel):
    profile_id: str


class SetMealRequest(BaseModel):
    profile_id: str
    meal: str


class RequestAssistanceRequest(BaseModel):
    profile_id: str
    note: str


# Инициализация state manager
def _create_airline_state_manager() -> AirlineStateManager | DynamoDBAirlineStateManager:
    """Создаёт соответствующий state manager на основе конфигурации окружения."""
    use_memory = os.environ.get("USE_MEMORY_STORE", "true").lower() == "true"

    if use_memory:
        logger.debug("Using AirlineStateManager (in-memory, no persistence)")
        return AirlineStateManager()
    else:
        # DynamoDB configuration
        region = os.environ.get("AWS_REGION", "us-east-1")
        table_prefix = os.environ.get("DYNAMODB_TABLE_PREFIX", "airline")
        endpoint_url = os.environ.get("DYNAMODB_ENDPOINT_URL")

        logger.debug(f"Using DynamoDBAirlineStateManager")
        logger.debug(f"   Region: {region}")
        logger.debug(f"   Table prefix: {table_prefix}")
        if endpoint_url:
            logger.debug(f"   Endpoint URL: {endpoint_url} (local DynamoDB)")

        state_manager = DynamoDBAirlineStateManager(
            region_name=region,
            table_prefix=table_prefix,
            endpoint_url=endpoint_url,
        )

        # Create table if AUTO_CREATE_TABLES=true
        if os.environ.get("AUTO_CREATE_TABLES", "false").lower() == "true":
            logger.debug("Creating DynamoDB airline profiles table...")
            state_manager.create_table()

        return state_manager


# Global state manager instance
_state_manager = _create_airline_state_manager()


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "airline-state-management"}


@app.get("/profile/{profile_id}")
async def get_customer_profile(profile_id: str) -> dict[str, Any]:
    """
    Получить профиль клиента по profile_id.
    
    Args:
        profile_id: Уникальный идентификатор профиля клиента
        
    Returns:
        Профиль клиента со всей информацией о рейсах, багаже и т.д.
    """
    try:
        profile = _state_manager.get_profile(profile_id)
        return {"success": True, "profile": profile.to_dict()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seat")
async def change_customer_seat(request: ChangeSeatRequest) -> dict[str, Any]:
    """
    Изменить место клиента на рейсе.
    
    Args:
        request: Запрос с profile_id, номером рейса и новым местом
        
    Returns:
        Сообщение об успешном изменении места
    """
    try:
        result = _state_manager.change_seat(
            request.profile_id,
            request.flight_number,
            request.seat
        )
        return {"success": True, "message": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cancel")
async def cancel_customer_trip(request: CancelTripRequest) -> dict[str, Any]:
    """
    Отменить поездку клиента.
    
    Args:
        request: Запрос с profile_id
        
    Returns:
        Сообщение об успешной отмене
    """
    try:
        result = _state_manager.cancel_trip(request.profile_id)
        return {"success": True, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bag")
async def add_customer_bag(request: AddBagRequest) -> dict[str, Any]:
    """
    Добавить багаж для клиента.
    
    Args:
        request: Запрос с profile_id
        
    Returns:
        Сообщение об успешном добавлении багажа
    """
    try:
        result = _state_manager.add_bag(request.profile_id)
        return {"success": True, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/meal")
async def set_customer_meal(request: SetMealRequest) -> dict[str, Any]:
    """
    Установить предпочтение по еде для клиента.
    
    Args:
        request: Запрос с profile_id и предпочтением по еде
        
    Returns:
        Сообщение об успешной установке предпочтения
    """
    try:
        result = _state_manager.set_meal(request.profile_id, request.meal)
        return {"success": True, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/assistance")
async def request_customer_assistance(request: RequestAssistanceRequest) -> dict[str, Any]:
    """
    Запросить специальную помощь для клиента.
    
    Args:
        request: Запрос с profile_id и примечанием о необходимой помощи
        
    Returns:
        Сообщение об успешной записи запроса на помощь
    """
    try:
        result = _state_manager.request_assistance(request.profile_id, request.note)
        return {"success": True, "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root() -> dict[str, Any]:
    """
    Корневой endpoint с информацией о сервисе.
    """
    return {
        "service": "Airline State Management API",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "get_profile": "GET /profile/{profile_id}",
            "change_seat": "POST /seat",
            "cancel_trip": "POST /cancel",
            "add_bag": "POST /bag",
            "set_meal": "POST /meal",
            "request_assistance": "POST /assistance"
        }
    }
