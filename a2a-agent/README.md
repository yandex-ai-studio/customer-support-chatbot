# A2A Customer Support Agent

Агент поддержки клиентов на основе Yandex AI Studio и протокола Agent-to-Agent (A2A).

## 📖 Содержание

- [Описание](#-описание)
- [Архитектура](#️-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Развертывание в Yandex Cloud](#-развертывание-в-yandex-cloud-подробная-инструкция)
  - [Шаг 1: Сборка Docker-образа](#шаг-1-сборка-docker-образа)
  - [Шаг 2: Container Registry](#шаг-2-создание-container-registry-и-загрузка-образа)
  - [Шаг 3: Сервисный аккаунт](#шаг-3-создание-сервисного-аккаунта-с-ролями)
  - [Шаг 4: API-ключ](#шаг-4-создание-api-ключа-с-необходимыми-скоупами)
  - [Шаг 5: Lockbox секрет](#шаг-5-создание-секрета-lockbox)
  - [Шаг 6: Деплой контейнера](#шаг-6-создание-serverless-container-и-деплой)
- [Переменные окружения](#-переменные-окружения)
- [Полезные ссылки](#-полезные-ссылки)

## 📋 Описание

A2A Customer Support Agent — это интеллектуальный агент службы поддержки для авиакомпании, построенный на базе:
- **Yandex AI Studio** для LLM, MCP-сервера и векторных хранилищ
- **A2A Protocol (Agent-to-Agent)** для межагентного взаимодействия
- **MCP (Model Context Protocol)** для интеграции с внешними инструментами
- **FileSearchTool** для поиска по векторному хранилищу
- **OpenAI Agents SDK** для реализации AI-агента

Агент помогает элитным пассажирам с:
- Изменением мест в самолёте
- Отменой и изменением бронирований
- Управлением багажом
- Специальными запросами

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                  A2A Client (другой агент)                  │
│                 или пользовательский интерфейс              │
└──────────────────────┬──────────────────────────────────────┘
                       │ A2A Protocol (HTTP/JSON)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Serverless Container (A2A Agent)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  A2A Starlette Server (__main__.py)                  │   │
│  │  - AgentCard (публичная карточка агента)             │   │
│  │  - AgentSkill (навыки и возможности)                 │   │
│  │  - DefaultRequestHandler (обработка запросов)        │   │
│  │  - InMemoryTaskStore (хранение задач)                │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  CustomerSupportAgentExecutor (executor.py)          │   │
│  │  - Обработка A2A запросов                            │   │
│  │  - Загрузка профиля клиента                          │   │
│  │  - Формирование контекста                            │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  Customer Support Agent (agent.py)                   │   │
│  │  - YandexGPT модель                                  │   │
│  │  - Инструкции для агента поддержки                   │   │
│  │  - File Search Tool (векторный поиск)                │   │
│  │  - MCP сервер для внешних инструментов               │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│  ┌────────────▼─────────────────────────────────────────┐   │
│  │  Airline Client (airline_client.py)                  │   │
│  │  - Загрузка профиля клиента                          │   │
│  │  - Форматирование контекста                          │   │
│  └─────────────┬────────────────────────────────────────┘   │
└────────────────┼────────────────────────────────────────────┘
                 │
         ┌───────┼───────────────────────┐
         │       │                       │
         ▼       ▼                       ▼
┌────────────┐ ┌──────────────────┐ ┌─────────────────┐
│ Airline    │ │  Responses API   │ │   MCP Server    │
│    API     │ │   (YandexGPT)    │ │  (Airline API)  │
│  (REST)    │ │                  │ │                 │
└────────────┘ └──────────────────┘ └─────────────────┘
```

### Компоненты

1. **A2A Starlette Server** - Реализация A2A протокола для межагентного взаимодействия
2. **Agent Executor** - Обработка запросов и оркестрация выполнения задач
3. **Customer Support Agent** - Логика агента на основе AI Studio Responses API
4. **Airline Client** - Интеграция с API авиакомпании для получения профилей
5. **InMemoryTaskStore** - Хранение активных задач в памяти

### Особенности A2A Agent

- **Stateless** - не требует хранения состояния между запросами (в отличие от chatkit-agent)
- **Agent Card** - публичная карточка с описанием навыков и возможностей агента
- **A2A Protocol** - стандартизированный протокол для межагентного взаимодействия
- **Task-based** - работа с задачами (tasks) вместо чатов (threads)
- **Event Queue** - потоковая отправка событий клиенту

## ⚡ Быстрый старт

Для быстрого развертывания выполните следующие команды:

```bash
# 1. Настройка переменных
export FOLDER_ID=$(yc config get folder-id)
export REGISTRY_NAME="my-registry"
export SA_NAME="a2a-agent-sa"

# 2. Сборка и загрузка образа
cd a2a-agent
docker build -t a2a-agent:latest .
yc container registry create --name ${REGISTRY_NAME}
REGISTRY_ID=$(yc container registry get --name ${REGISTRY_NAME} --format json | jq -r '.id')
yc container registry configure-docker
docker tag a2a-agent:latest cr.yandex/${REGISTRY_ID}/a2a-agent:latest
docker push cr.yandex/${REGISTRY_ID}/a2a-agent:latest

# 3. Настройка сервисного аккаунта и API-ключа
yc iam service-account create --name ${SA_NAME}
SA_ID=$(yc iam service-account get ${SA_NAME} --format json | jq -r '.id')

# Назначение ролей (одной командой)
yc resourcemanager folder add-access-bindings ${FOLDER_ID} \
  --access-binding role=lockbox.payloadViewer,subject=serviceAccount:${SA_ID} \
  --access-binding role=container-registry.images.puller,subject=serviceAccount:${SA_ID} \
  --access-binding role=serverless.containers.invoker,subject=serviceAccount:${SA_ID} \
  --access-binding role=serverless.mcpGateways.invoker,subject=serviceAccount:${SA_ID} \
  --access-binding role=ai.assistants.editor,subject=serviceAccount:${SA_ID} \
  --access-binding role=ai.languageModels.user,subject=serviceAccount:${SA_ID}

# Создание API-ключа и секрета
API_KEY=$(yc iam api-key create --service-account-id ${SA_ID} \
  --scope "yc.ai.languageModels.execute" \
  --scope "yc.serverless.containers.invoke" \
  --scope "yc.serverless.mcpGateways.invoke" \
  --format json | jq -r '.secret')
yc lockbox secret create --name a2a-api-key --payload "[{'key': 'API_KEY', 'text_value': '${API_KEY}'}]"
SECRET_ID=$(yc lockbox secret get a2a-api-key --format json | jq -r '.id')
VERSION_ID=$(yc lockbox secret get a2a-api-key --format json | jq -r '.current_version.id')

# 4. Получение URL MCP и Airline API
MCP_SERVER_URL="https://your-airline-mcp-server-url.com"
AIRLINE_API_URL="https://your-airline-api-url.com"

# 5. Создание векторного хранилища (опционально)
VECTOR_STORE_ID=""

# 6. Деплой контейнера
yc serverless container create --name a2a-agent
yc serverless container revision deploy \
  --container-name a2a-agent \
  --image cr.yandex/${REGISTRY_ID}/a2a-agent:latest \
  --service-account-id ${SA_ID} \
  --memory 1GB --cores 1 --execution-timeout 60s --concurrency 4 \
  --environment FOLDER_ID=${FOLDER_ID} \
  --environment MCP_SERVER_URL=${MCP_SERVER_URL} \
  --environment AIRLINE_API_URL=${AIRLINE_API_URL} \
  --environment VECTOR_STORE_ID=${VECTOR_STORE_ID} \
  --secret environment-variable=API_KEY,id=${SECRET_ID},version-id=${VERSION_ID},key=API_KEY

yc serverless container allow-unauthenticated-invoke a2a-agent

# 7. Получить URL
echo "A2A Agent URL: $(yc serverless container get a2a-agent --format json | jq -r '.url')"
```

> **Примечание**: Эта команда создает базовую конфигурацию. См. подробную инструкцию ниже для полной настройки.

## 🚀 Развертывание в Yandex Cloud (подробная инструкция)

Эта инструкция описывает полный процесс развертывания A2A агента в Yandex Cloud Serverless Containers.

### Предварительные требования

- Установленный [Yandex Cloud CLI](https://cloud.yandex.ru/docs/cli/quickstart)
- Docker для сборки образа
- Права на создание ресурсов в Yandex Cloud
- Развернутый Airline API MCP сервер (см. `../airline-api/README.md`)

### Шаг 1: Сборка Docker-образа

Соберите Docker-образ агента:

```bash
cd a2a-agent

# Сборка образа
docker build -t a2a-agent:latest .
```

### Шаг 2: Создание Container Registry и загрузка образа

Создайте реестр Container Registry и загрузите в него образ:

```bash
# Создание реестра
yc container registry create --name my-registry

# Получение ID реестра
REGISTRY_ID=$(yc container registry get --name my-registry --format json | jq -r '.id')

# Авторизация в Container Registry
yc container registry configure-docker

# Тегирование образа
docker tag a2a-agent:latest cr.yandex/${REGISTRY_ID}/a2a-agent:latest

# Загрузка образа
docker push cr.yandex/${REGISTRY_ID}/a2a-agent:latest
```

### Шаг 3: Создание сервисного аккаунта с ролями

Создайте сервисный аккаунт и назначьте ему необходимые роли:

```bash
# Создание сервисного аккаунта
yc iam service-account create --name a2a-agent-sa --description "Service account for A2A agent"

# Получение ID сервисного аккаунта
SA_ID=$(yc iam service-account get a2a-agent-sa --format json | jq -r '.id')

# Получение ID каталога
FOLDER_ID=$(yc config get folder-id)

# Назначение ролей (одной командой)
yc resourcemanager folder add-access-bindings ${FOLDER_ID} \
  --access-binding role=lockbox.payloadViewer,subject=serviceAccount:${SA_ID} \
  --access-binding role=container-registry.images.puller,subject=serviceAccount:${SA_ID} \
  --access-binding role=serverless.containers.invoker,subject=serviceAccount:${SA_ID} \
  --access-binding role=serverless.mcpGateways.invoker,subject=serviceAccount:${SA_ID} \
  --access-binding role=ai.assistants.editor,subject=serviceAccount:${SA_ID} \
  --access-binding role=ai.languageModels.user,subject=serviceAccount:${SA_ID}
```

> **Примечание**: A2A агент не требует роли `ydb.editor`, так как не использует YDB для хранения состояния.

### Шаг 4: Создание API-ключа с необходимыми скоупами

Создайте API-ключ для сервисного аккаунта с необходимыми правами:

```bash
# Создание API-ключа со скоупами и извлечение секрета
API_KEY=$(yc iam api-key create \
  --service-account-id ${SA_ID} \
  --description "API key for A2A agent" \
  --scope "yc.ai.languageModels.execute" \
  --scope "yc.serverless.containers.invoke" \
  --scope "yc.serverless.mcpGateways.invoke" \
  --format json | jq -r '.secret')

echo "API Key: ${API_KEY}"
```

> **Важно**: Сохраните `API_KEY` в безопасном месте. Он будет нужен для создания секрета Lockbox.

### Шаг 5: Создание секрета Lockbox

Создайте секрет в Yandex Lockbox для хранения API-ключа:

```bash
# Создание секрета с API-ключом
yc lockbox secret create \
  --name a2a-api-key \
  --description "API key for A2A agent" \
  --payload "[{'key': 'API_KEY', 'text_value': '${API_KEY}'}]"

# Получение ID секрета
SECRET_ID=$(yc lockbox secret get a2a-api-key --format json | jq -r '.id')
VERSION_ID=$(yc lockbox secret get a2a-api-key --format json | jq -r '.current_version.id')

echo "Secret ID: ${SECRET_ID}"
```

### Шаг 6: Создание Serverless Container и деплой

Создайте публичный Serverless Container и разверните ревизию:

```bash
# Получение переменных из предыдущих шагов
FOLDER_ID=$(yc config get folder-id)
REGISTRY_ID=$(yc container registry get --name my-registry --format json | jq -r '.id')
SA_ID=$(yc iam service-account get a2a-agent-sa --format json | jq -r '.id')
SECRET_ID=$(yc lockbox secret get a2a-api-key --format json | jq -r '.id')
VERSION_ID=$(yc lockbox secret get a2a-api-key --format json | jq -r '.current_version.id')

# Получение URL MCP сервера (должен быть развернут заранее)
MCP_SERVER_URL=$(yc serverless container get airline-api --format json | jq -r '.url')

# Получение URL Airline API
AIRLINE_API_URL=${MCP_SERVER_URL}

# Создание векторного хранилища (опционально)
# Если не используется File Search, оставьте VECTOR_STORE_ID пустым
VECTOR_STORE_ID=""

# Создание контейнера
yc serverless container create --name a2a-agent

# Деплой ревизии контейнера
yc serverless container revision deploy \
  --container-name a2a-agent \
  --image cr.yandex/${REGISTRY_ID}/a2a-agent:latest \
  --service-account-id ${SA_ID} \
  --memory 1GB \
  --cores 1 \
  --execution-timeout 60s \
  --concurrency 4 \
  --environment FOLDER_ID=${FOLDER_ID} \
  --environment MCP_SERVER_URL=${MCP_SERVER_URL} \
  --environment AIRLINE_API_URL=${AIRLINE_API_URL} \
  --environment VECTOR_STORE_ID=${VECTOR_STORE_ID} \
  --secret environment-variable=API_KEY,id=${SECRET_ID},version-id=${VERSION_ID},key=API_KEY

# Сделать контейнер публичным
yc serverless container allow-unauthenticated-invoke a2a-agent

# Получить URL контейнера
CONTAINER_URL=$(yc serverless container get a2a-agent --format json | jq -r '.url')

echo "A2A Agent URL: ${CONTAINER_URL}"
```

### Проверка развертывания

Проверьте, что агент работает корректно:

```bash
# Получение Agent Card
curl ${CONTAINER_URL}/.well-known/ai-agent.json

# Создание задачи (A2A протокол)
curl -X POST ${CONTAINER_URL}/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      {
        "role": "user",
        "parts": [
          {
            "text": "I need to change my seat on flight AA123"
          }
        ]
      }
    ],
    "context": {
      "context_id": "customer_12345"
    }
  }'
```

## 📝 Переменные окружения

Полный список переменных окружения для Serverless Container:

| Переменная | Обязательная | Описание |
|------------|--------------|----------|
| `API_KEY` | Да | API-ключ Yandex Cloud (из Lockbox) |
| `FOLDER_ID` | Да | ID каталога Yandex Cloud |
| `MCP_SERVER_URL` | Да | URL MCP сервера (Airline API) |
| `AIRLINE_API_URL` | Да | URL REST API авиакомпании для профилей |
| `VECTOR_STORE_ID` | Нет | ID векторного хранилища для File Search |
| `PORT` | Нет | Порт для HTTP сервера (по умолчанию 9999) |
| `SERVER_URL` | Нет | Публичный URL агента (для Agent Card) |

## 📡 A2A Protocol

### Agent Card

Агент предоставляет публичную карточку (Agent Card) по адресу `/.well-known/ai-agent.json`:

```json
{
  "name": "Customer Support Agent",
  "description": "Airline customer support agent for elite travelers",
  "url": "https://your-container-url.com",
  "version": "1.0.0",
  "default_input_modes": ["text"],
  "default_output_modes": ["text"],
  "capabilities": {},
  "skills": [
    {
      "id": "customer_support",
      "name": "Airline Customer Support",
      "description": "Airline customer support: seat changes, flight cancellations, baggage, and special requests",
      "tags": ["customer support", "airline", "booking"],
      "examples": [
        "I want to change my seat",
        "Help me cancel my flight",
        "I need additional assistance",
        "What is my loyalty status?"
      ]
    }
  ]
}
```

### Создание задачи

```bash
POST /tasks
Content-Type: application/json

{
  "input": [
    {
      "role": "user",
      "parts": [
        {
          "text": "User message here"
        }
      ]
    }
  ],
  "context": {
    "context_id": "customer_id"
  }
}
```

### Получение статуса задачи

```bash
GET /tasks/{task_id}
```

### Интеграция с другими агентами

A2A протокол позволяет агентам взаимодействовать друг с другом:

```python
import httpx

async def call_support_agent(customer_id: str, message: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{A2A_AGENT_URL}/tasks",
            json={
                "input": [
                    {
                        "role": "user",
                        "parts": [{"text": message}]
                    }
                ],
                "context": {"context_id": customer_id}
            }
        )
        return response.json()
```

## 🆚 Сравнение с ChatKit Agent

| Характеристика | A2A Agent | ChatKit Agent |
|----------------|-----------|---------------|
| Протокол | A2A (Agent-to-Agent) | OpenAI ChatKit |
| Хранилище | InMemoryTaskStore | YDB Document API |
| Состояние | Stateless | Stateful (история чатов) |
| API | Tasks-based | Threads/Messages |
| Использование | Agent-to-Agent взаимодействие | Пользовательские чат-интерфейсы |
| Сложность развертывания | Ниже (не требует YDB) | Выше (требует YDB) |

## 🔧 Локальная разработка

### Настройка окружения

Создайте файл `.env`:

```bash
FOLDER_ID=your-folder-id
API_KEY=your-api-key
MCP_SERVER_URL=http://localhost:8001
AIRLINE_API_URL=http://localhost:8001
VECTOR_STORE_ID=
PORT=9999
```

### Запуск локально

```bash
# Установка зависимостей
uv sync

# Запуск сервера
uv run python -m app
```

### Тестирование

```bash
# Получение Agent Card
curl http://localhost:9999/.well-known/ai-agent.json

# Создание задачи
curl -X POST http://localhost:9999/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "input": [
      {
        "role": "user",
        "parts": [{"text": "Hello, I need help"}]
      }
    ],
    "context": {"context_id": "test_customer"}
  }'
```

## 📚 Полезные ссылки

### Документация Yandex Cloud
- [Serverless Containers](https://cloud.yandex.ru/docs/serverless-containers/)
- [IAM токены](https://cloud.yandex.ru/docs/iam/concepts/authorization/iam-token)
- [Сервисные аккаунты](https://cloud.yandex.ru/docs/iam/concepts/users/service-accounts)
- [Container Registry](https://cloud.yandex.ru/docs/container-registry/)
- [Lockbox](https://cloud.yandex.ru/docs/lockbox/)
- [API-ключи](https://cloud.yandex.ru/docs/iam/concepts/authorization/api-key)

### Документация Yandex AI Studio
- [AI-агенты документация](https://yandex.cloud/ru/docs/ai-studio/concepts/agents/)
- [LLM модели](https://yandex.cloud/ru/docs/ai-studio/concepts/generation/)
- [Векторные хранилища](https://yandex.cloud/ru/docs/ai-studio/concepts/search/vectorstore)
- [MCP Hub](https://yandex.cloud/ru/docs/ai-studio/concepts/mcp-hub/)

### Документация A2A Protocol
- [A2A SDK](https://github.com/openai/agent-to-agent)
- [A2A Protocol Specification](https://spec.a2a.ai/)
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи контейнера: `yc serverless container revision logs <REVISION_ID>`
2. Убедитесь, что все переменные окружения заданы правильно
3. Проверьте доступность MCP сервера и Airline API
4. Убедитесь, что сервисный аккаунт имеет все необходимые роли

