# Airline API

REST API микросервис для управления профилями клиентов авиакомпании и состоянием бронирований.

## 📖 Содержание

- [Описание](#-описание)
- [Архитектура](#️-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Развертывание в Yandex Cloud](#-развертывание-в-yandex-cloud-подробная-инструкция)
  - [Шаг 1: Сборка Docker-образа](#шаг-1-сборка-docker-образа)
  - [Шаг 2: Container Registry](#шаг-2-создание-container-registry-и-загрузка-образа)
  - [Шаг 3: YDB Document API (опционально)](#шаг-3-создание-базы-данных-ydb-document-api-опционально)
  - [Шаг 4: Сервисный аккаунт](#шаг-4-создание-сервисного-аккаунта-с-ролями)
  - [Шаг 5: API-ключ](#шаг-5-создание-api-ключа)
  - [Шаг 6: Lockbox секрет](#шаг-6-создание-секрета-lockbox)
  - [Шаг 7: MCP Gateway](#шаг-7-создание-mcp-gateway-опционально)
  - [Шаг 8: Деплой контейнера](#шаг-8-создание-serverless-container-и-деплой)
- [API Endpoints](#-api-endpoints)
- [Переменные окружения](#-переменные-окружения)
- [Интеграция с MCP](#-интеграция-с-mcp)
- [Полезные ссылки](#-полезные-ссылки)

## 📋 Описание

Airline API — это микросервис для управления состоянием клиентов авиакомпании:
- **REST API** для CRUD операций с профилями клиентов
- **YDB Document API** (опционально) для персистентного хранения данных
- **In-Memory хранилище** для быстрой разработки и тестирования
- **MCP Gateway интеграция** для использования в качестве инструментов AI агентов
- **Независимый микросервис** без зависимостей от других компонентов системы

Основные возможности:
- Управление профилями клиентов (имя, email, телефон, статус лояльности)
- Управление сегментами рейсов (origin, destination, seat, status)
- Изменение мест в самолёте
- Отмена бронирований
- Управление багажом
- Установка предпочтений по питанию
- Запросы на специальную помощь
- Временная шкала действий (timeline) по каждому профилю

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend / ChatKit Agent                   │
│                       или A2A Agent                         │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Serverless Container (Airline API)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (main.py)                            │   │
│  │  - GET  /profile/{profile_id}                        │   │
│  │  - POST /seat (изменить место)                       │   │
│  │  - POST /cancel (отменить бронирование)              │   │
│  │  - POST /bag (добавить багаж)                        │   │
│  │  - POST /meal (предпочтения питания)                 │   │
│  │  - POST /assistance (запрос помощи)                  │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  Airline State Manager (airline_state.py)            │   │
│  │  - CustomerProfile (модель данных)                   │   │
│  │  - FlightSegment (модель сегмента рейса)             │   │
│  │  - Бизнес-логика операций                            │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│       ┌───────┴────────┐                                    │
│       ▼                ▼                                    │
│  ┌─────────┐    ┌──────────────┐                            │
│  │ Memory  │    │   DynamoDB   │                            │
│  │ Storage │    │ (YDB Doc API)│                            │
│  └─────────┘    └──────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   MCP Gateway   │
              │  (AI Studio)    │
              │  - SSE Stream   │
              │  - Tool calling │
              └─────────────────┘
```

### Компоненты

1. **FastAPI Server** - REST API с endpoints для управления профилями
2. **Airline State Manager** - Бизнес-логика и модели данных
3. **Storage Layer** - Выбор между in-memory и DynamoDB (YDB Document API)
4. **MCP Gateway** - Интеграция с AI Studio для оборачивания в MCP-сервер

### Модели данных

**CustomerProfile:**
- `customer_id` - уникальный идентификатор
- `name` - имя клиента
- `loyalty_status` - статус программы лояльности
- `loyalty_id` - ID в программе лояльности
- `email` - электронная почта
- `phone` - телефон
- `tier_benefits` - список привилегий
- `segments` - список сегментов рейсов
- `bags_checked` - количество зарегистрированного багажа
- `meal_preference` - предпочтения по питанию
- `special_assistance` - заметки о специальной помощи
- `timeline` - временная шкала действий

**FlightSegment:**
- `flight_number` - номер рейса
- `date` - дата рейса
- `origin` - аэропорт отправления
- `destination` - аэропорт назначения
- `departure_time` - время вылета
- `arrival_time` - время прибытия
- `seat` - место в самолёте
- `status` - статус рейса (Scheduled/Cancelled)

## ⚡ Быстрый старт

### Локальная разработка

```bash
# 1. Установка зависимостей
cd airline-api
uv sync

# 2. Запуск с in-memory хранилищем (для разработки)
export USE_MEMORY_STORE=true
export PORT=8001
uv run uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

# 3. Проверка работы
curl http://localhost:8001/health
curl http://localhost:8001/profile/demo_default_thread
```

### С использованием Docker

```bash
# Сборка образа
docker build -t airline-api:latest .

# Запуск контейнера
docker run -p 8001:8001 \
  -e PORT=8001 \
  -e USE_MEMORY_STORE=true \
  airline-api:latest
```

## 🚀 Развертывание в Yandex Cloud (подробная инструкция)

Эта инструкция описывает полный процесс развертывания Airline API в Yandex Cloud Serverless Containers с интеграцией через MCP Gateway.

### Предварительные требования

- Установленный [Yandex Cloud CLI](https://cloud.yandex.ru/docs/cli/quickstart)
- Docker для сборки образа
- Права на создание ресурсов в Yandex Cloud

### Шаг 1: Сборка Docker-образа

Соберите Docker-образ API:

```bash
cd airline-api

# Сборка образа
docker build -t airline-api:latest .
```

### Шаг 2: Создание Container Registry и загрузка образа

Создайте реестр Container Registry и загрузите в него образ:

```bash
# Создание реестра (если ещё не создан)
yc container registry create --name my-registry

# Получение ID реестра
REGISTRY_ID=$(yc container registry get --name my-registry --format json | jq -r '.id')

# Авторизация в Container Registry
yc container registry configure-docker

# Тегирование образа
docker tag airline-api:latest cr.yandex/${REGISTRY_ID}/airline-api:latest

# Загрузка образа
docker push cr.yandex/${REGISTRY_ID}/airline-api:latest
```

### Шаг 3: Создание базы данных YDB Document API (опционально)

> **Примечание**: Для разработки можно использовать in-memory хранилище (`USE_MEMORY_STORE=true`). Для production рекомендуется YDB.

Создайте Serverless YDB базу данных с поддержкой Document API:

```bash
# Создание Serverless YDB
yc ydb database create \
  --name airline-db \
  --serverless

# Получение Document API endpoint
DOCUMENT_API_ENDPOINT=$(yc ydb database get airline-db --format json | jq -r '.document_api_endpoint')

echo "Document API Endpoint: ${DOCUMENT_API_ENDPOINT}"
```

> **Примечание**: Сохраните значение `DOCUMENT_API_ENDPOINT` - оно понадобится для настройки переменных окружения.

### Шаг 4: Создание сервисного аккаунта с ролями

Создайте сервисный аккаунт и назначьте ему необходимые роли:

```bash
# Создание сервисного аккаунта
yc iam service-account create --name airline-api-sa --description "Service account for Airline API"

# Получение ID сервисного аккаунта
SA_ID=$(yc iam service-account get airline-api-sa --format json | jq -r '.id')

# Получение ID каталога
FOLDER_ID=$(yc config get folder-id)

# Назначение ролей
yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role lockbox.payloadViewer \
  --subject serviceAccount:${SA_ID}

yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role container-registry.images.puller \
  --subject serviceAccount:${SA_ID}

yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role serverless.containers.invoker \
  --subject serviceAccount:${SA_ID}

# Если используется YDB
yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role ydb.editor \
  --subject serviceAccount:${SA_ID}
```

### Шаг 5: Создание API-ключа

Создайте API-ключ для сервисного аккаунта:

```bash
# Создание API-ключа
yc iam api-key create \
  --service-account-id ${SA_ID} \
  --description "API key for Airline API" \
  --format json > airline-api-key.json

# Извлечение секретного ключа
API_KEY=$(cat airline-api-key.json | jq -r '.secret')

echo "API Key: ${API_KEY}"
```

> **Важно**: Сохраните `API_KEY` в безопасном месте.

### Шаг 6: Создание секрета Lockbox

Создайте секрет в Yandex Lockbox для хранения API-ключа:

```bash
# Создание секрета с API-ключом
yc lockbox secret create \
  --name airline-api-key \
  --description "API key for Airline API" \
  --payload "[{'key': 'API_KEY', 'text_value': '${API_KEY}'}]"

# Получение ID секрета
SECRET_ID=$(yc lockbox secret get airline-api-key --format json | jq -r '.id')

echo "Secret ID: ${SECRET_ID}"
```

### Шаг 7: Создание MCP Gateway (опционально)

MCP Gateway позволяет AI агентам использовать Airline API как набор инструментов:

```bash
# Сначала создайте контейнер (см. Шаг 8), затем создайте MCP Gateway

# Получение URL контейнера
CONTAINER_URL=$(yc serverless container get airline-api --format json | jq -r '.url')

# Создание MCP Gateway
yc ai mcp-gateway create \
  --name airline-tools \
  --service-account-id ${SA_ID} \
  --sse-url ${CONTAINER_URL}/sse \
  --sse-headers "Authorization: Api-Key ${API_KEY}"

# Получение ID MCP Gateway
MCP_GATEWAY_ID=$(yc ai mcp-gateway get airline-tools --format json | jq -r '.id')

# URL для использования в агентах
MCP_SERVER_URL="https://${MCP_GATEWAY_ID}.6q7pzfrg.mcpgw.serverless.yandexcloud.net/sse"

echo "MCP Server URL: ${MCP_SERVER_URL}"
```

> **Примечание**: MCP Gateway нужен только если вы хотите использовать API как инструменты для AI агентов через AI Studio MCP Hub.

### Шаг 8: Создание и развертывание Serverless Container

Создайте публичный Serverless Container и разверните ревизию:

```bash
# Создание контейнера
yc serverless container create --name airline-api

# Вариант 1: Деплой с in-memory хранилищем (для разработки)
yc serverless container revision deploy \
  --container-name airline-api \
  --image cr.yandex/${REGISTRY_ID}/airline-api:latest \
  --service-account-id ${SA_ID} \
  --memory 512MB \
  --cores 1 \
  --execution-timeout 30s \
  --concurrency 4 \
  --environment PORT=8001 \
  --environment USE_MEMORY_STORE=true \
  --secret environment-variable=API_KEY,id=${SECRET_ID},version-id=latest,key=API_KEY

# Вариант 2: Деплой с YDB Document API (для production)
yc serverless container revision deploy \
  --container-name airline-api \
  --image cr.yandex/${REGISTRY_ID}/airline-api:latest \
  --service-account-id ${SA_ID} \
  --memory 512MB \
  --cores 1 \
  --execution-timeout 30s \
  --concurrency 4 \
  --environment PORT=8001 \
  --environment USE_MEMORY_STORE=false \
  --environment AWS_REGION=ru-central1 \
  --environment DYNAMODB_ENDPOINT_URL=${DOCUMENT_API_ENDPOINT} \
  --environment DYNAMODB_TABLE_PREFIX=airline \
  --environment AUTO_CREATE_TABLES=true \
  --secret environment-variable=API_KEY,id=${SECRET_ID},version-id=latest,key=API_KEY

# Сделать контейнер публичным
yc serverless container allow-unauthenticated-invoke airline-api

# Получить URL контейнера
CONTAINER_URL=$(yc serverless container get airline-api --format json | jq -r '.url')

echo "Container URL: ${CONTAINER_URL}"
```

### Проверка развертывания

Проверьте, что API работает корректно:

```bash
# Health check
curl ${CONTAINER_URL}/health

# Получение профиля
curl ${CONTAINER_URL}/profile/demo_default_thread

# Список всех endpoints
curl ${CONTAINER_URL}/

# Изменение места
curl -X POST ${CONTAINER_URL}/seat \
  -H "Content-Type: application/json" \
  -H "Authorization: Api-Key ${API_KEY}" \
  -d '{
    "profile_id": "demo_default_thread",
    "flight_number": "OA476",
    "seat": "14C"
  }'
```

## 📡 API Endpoints

### GET /health
Health check endpoint.

```bash
curl http://localhost:8001/health
```

Response:
```json
{
  "status": "healthy",
  "service": "airline-state-management"
}
```

### GET /profile/{profile_id}
Получить профиль клиента по profile_id.

```bash
curl http://localhost:8001/profile/demo_default_thread
```

Response:
```json
{
  "success": true,
  "profile": {
    "customer_id": "demo_default_thread",
    "name": "Jordan Miles",
    "loyalty_status": "Aviator Platinum",
    "loyalty_id": "APL-204981",
    "email": "jordan.miles@example.com",
    "phone": "+1 (415) 555-9214",
    "tier_benefits": [
      "Complimentary upgrades when available",
      "Unlimited lounge access",
      "Priority boarding group 1"
    ],
    "segments": [...],
    "bags_checked": 0,
    "meal_preference": null,
    "special_assistance": null,
    "timeline": [...]
  }
}
```

### POST /seat
Изменить место клиента на рейсе.

```bash
curl -X POST http://localhost:8001/seat \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "demo_default_thread",
    "flight_number": "OA476",
    "seat": "14C"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Seat updated to 14C on flight OA476."
}
```

### POST /cancel
Отменить поездку клиента.

```bash
curl -X POST http://localhost:8001/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "demo_default_thread"
  }'
```

Response:
```json
{
  "success": true,
  "message": "The reservation has been cancelled. Refund processing will begin immediately."
}
```

### POST /bag
Добавить багаж для клиента.

```bash
curl -X POST http://localhost:8001/bag \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "demo_default_thread"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Checked bag added. You now have 1 bag(s) checked."
}
```

### POST /meal
Установить предпочтение по еде для клиента.

```bash
curl -X POST http://localhost:8001/meal \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "demo_default_thread",
    "meal": "vegetarian"
  }'
```

Response:
```json
{
  "success": true,
  "message": "We'll note vegetarian as the meal preference."
}
```

### POST /assistance
Запросить специальную помощь для клиента.

```bash
curl -X POST http://localhost:8001/assistance \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": "demo_default_thread",
    "note": "Wheelchair assistance needed"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Assistance request recorded. Airport staff will be notified."
}
```

### GET /
Корневой endpoint с информацией о сервисе.

```bash
curl http://localhost:8001/
```

Response:
```json
{
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
```

## 📝 Переменные окружения

Полный список переменных окружения для Serverless Container:

| Переменная | Обязательная | Значение по умолчанию | Описание |
|------------|--------------|----------------------|----------|
| `PORT` | Да | - | Порт для HTTP сервера (обычно 8001) |
| `USE_MEMORY_STORE` | Да | `true` | `true` для in-memory, `false` для DynamoDB |
| `AWS_REGION` | Нет* | `us-east-1` | Регион для DynamoDB (для Yandex Cloud: `ru-central1`) |
| `DYNAMODB_ENDPOINT_URL` | Нет* | - | URL Document API endpoint (YDB) |
| `DYNAMODB_TABLE_PREFIX` | Нет | `airline` | Префикс для таблиц DynamoDB |
| `AUTO_CREATE_TABLES` | Нет | `false` | Автоматическое создание таблиц при запуске |
| `API_KEY` | Нет** | - | API-ключ для аутентификации запросов |

\* Обязательные если `USE_MEMORY_STORE=false`  
\** Обязательный если требуется аутентификация или для использования с MCP Gateway

## 🔧 Интеграция с MCP

Airline API можно использовать как MCP-сервер для AI агентов через Yandex AI Studio MCP Hub.

### Что такое MCP?

Model Context Protocol (MCP) - это протокол для интеграции внешних инструментов (tools) с AI агентами. Airline API предоставляет следующие инструменты:

1. **get_customer_profile** - Получить профиль клиента
2. **change_seat** - Изменить место на рейсе
3. **cancel_trip** - Отменить бронирование
4. **add_checked_bag** - Добавить багаж
5. **set_meal_preference** - Установить предпочтения питания
6. **request_assistance** - Запросить специальную помощь

### Использование через MCP Gateway

После создания MCP Gateway (см. Шаг 7), используйте его URL в агентах:

```python
from agents.mcp import MCPServerSse

# URL MCP Gateway
MCP_SERVER_URL = "https://<gateway-id>.mcpgw.serverless.yandexcloud.net/sse"

# Создание MCP клиента
mcp_server = MCPServerSse(
    params={
        "url": MCP_SERVER_URL,
        "headers": {
            "Authorization": f"Api-Key {API_KEY}"
        }
    },
    name="Airline Tools"
)

# Использование в агенте
await mcp_server.connect()
tools = await mcp_server.list_tools()
```

### Прямое использование как MCP сервер

Airline API также может работать как standalone MCP сервер через SSE:

```python
import httpx

# Подключение к SSE endpoint
async with httpx.AsyncClient() as client:
    async with client.stream(
        "GET",
        f"{AIRLINE_API_URL}/sse",
        headers={"Authorization": f"Api-Key {API_KEY}"}
    ) as response:
        async for line in response.aiter_lines():
            # Обработка SSE событий
            print(line)
```

## 🔐 Аутентификация

Airline API поддерживает аутентификацию через API-ключи:

```bash
# Запросы с API-ключом
curl http://localhost:8001/profile/test \
  -H "Authorization: Api-Key your_api_key_here"
```

Для локальной разработки можно отключить проверку API-ключей (по умолчанию отключена).

## 🧪 Тестирование

### Ручное тестирование

```bash
# Получить профиль
curl http://localhost:8001/profile/test_user

# Изменить место
curl -X POST http://localhost:8001/seat \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "test_user", "flight_number": "OA476", "seat": "15F"}'

# Проверить изменения
curl http://localhost:8001/profile/test_user
```

### Управление DynamoDB

Если используется YDB Document API, управляйте таблицами с помощью скрипта:

```bash
cd airline-api/app/dynamodb

# Создать таблицы
python manage_airline_db.py --create

# Проверить статус
python manage_airline_db.py --status

# Список профилей
python manage_airline_db.py --list-profiles

# Получить конкретный профиль
python manage_airline_db.py --get-profile demo_default_thread

# Удалить все данные (⚠️ ОСТОРОЖНО)
python manage_airline_db.py --delete
```

## 📊 Мониторинг и логи

### Просмотр логов контейнера

```bash
# Получить ID последней ревизии
REVISION_ID=$(yc serverless container revision list \
  --container-name airline-api \
  --format json | jq -r '.[0].id')

# Просмотреть логи
yc serverless container revision logs ${REVISION_ID}

# Следить за логами в реальном времени
yc serverless container revision logs ${REVISION_ID} --follow
```

### Метрики

Yandex Cloud автоматически собирает метрики:
- Количество запросов
- Время выполнения
- Ошибки
- Использование ресурсов

Просмотр метрик в [консоли Yandex Cloud](https://console.cloud.yandex.ru/).

## 🚨 Устранение неполадок

### CORS ошибки

Если фронтенд получает CORS ошибки при обращении к Airline API в Yandex Cloud:

**Решение**: Используйте proxy через chatkit-agent вместо прямого обращения.

```typescript
// Неправильно - прямое обращение к Airline API
const response = await fetch('https://airline-api.yandexcloud.net/profile/user');

// Правильно - через chatkit-agent proxy
const response = await fetch('http://localhost:8000/profiles/user');
```

### Проблемы с YDB Document API

```bash
# Проверьте endpoint
echo $DYNAMODB_ENDPOINT_URL

# Проверьте роли сервисного аккаунта
yc iam service-account list-access-bindings airline-api-sa

# Проверьте таблицы
python app/dynamodb/manage_airline_db.py --status
```

### Ошибки аутентификации

```bash
# Проверьте API-ключ в Lockbox
yc lockbox secret get airline-api-key

# Проверьте переменные окружения контейнера
yc serverless container revision get <REVISION_ID>
```

## 📚 Полезные ссылки

### Документация Yandex Cloud
- [Serverless Containers](https://cloud.yandex.ru/docs/serverless-containers/)
- [YDB Document API](https://cloud.yandex.ru/docs/ydb/docapi/)
- [Container Registry](https://cloud.yandex.ru/docs/container-registry/)
- [Lockbox](https://cloud.yandex.ru/docs/lockbox/)
- [IAM токены](https://cloud.yandex.ru/docs/iam/concepts/authorization/iam-token)
- [Сервисные аккаунты](https://cloud.yandex.ru/docs/iam/concepts/users/service-accounts)

### Документация Yandex AI Studio
- [MCP Hub](https://yandex.cloud/ru/docs/ai-studio/concepts/mcp-hub/)
- [MCP Gateway](https://yandex.cloud/ru/docs/ai-studio/operations/mcp-gateway/)
- [AI-агенты документация](https://yandex.cloud/ru/docs/ai-studio/concepts/agents/)

### Документация FastAPI
- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [Uvicorn](https://www.uvicorn.org/)

### Документация MCP
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи контейнера: `yc serverless container revision logs <REVISION_ID>`
2. Убедитесь, что все переменные окружения заданы правильно
3. Проверьте доступность YDB Document API (если используется)
4. Убедитесь, что сервисный аккаунт имеет все необходимые роли
5. Проверьте CORS настройки для фронтенд интеграции
