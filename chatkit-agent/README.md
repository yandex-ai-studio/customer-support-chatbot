# ChatKit Customer Support Agent

Агент поддержки клиентов на основе Yandex AI Studio и OpenAI ChatKit.

## 📖 Содержание

- [Описание](#-описание)
- [Архитектура](#️-архитектура)
- [Быстрый старт](#-быстрый-старт)
- [Развертывание в Yandex Cloud](#-развертывание-в-yandex-cloud-подробная-инструкция)
  - [Шаг 1: Сборка Docker-образа](#шаг-1-сборка-docker-образа)
  - [Шаг 2: Container Registry](#шаг-2-создание-container-registry-и-загрузка-образа)
  - [Шаг 3: YDB Document API](#шаг-3-создание-базы-данных-ydb-document-api)
  - [Шаг 4: Сервисный аккаунт](#шаг-4-создание-сервисного-аккаунта-с-ролями)
  - [Шаг 5: API-ключ](#шаг-5-создание-api-ключа-с-необходимыми-скоупами)
  - [Шаг 6: Lockbox секрет](#шаг-6-создание-секрета-lockbox)
  - [Шаг 7: Деплой контейнера](#шаг-7-создание-serverless-container-и-деплой)
- [Переменные окружения](#-переменные-окружения)
- [Полезные ссылки](#-полезные-ссылки)

## 📋 Описание

ChatKit Customer Support Agent — это интеллектуальный агент службы поддержки для авиакомпании, построенный на базе:
- **Yandex AI Studio** для LLM, MCP-сервера и векторных хранилищ
- **YDB Document API** (Serverless) для хранения истории чатов и сессий
- **MCP (Model Context Protocol)** для интеграции с внешними инструментами
- **FileSearchTool** для поиска по векторному хранилищу
- **OpenAI Agents SDK** для реализации AI-агента в целом
- **OpenAI ChatKit** для реализации чат-интерфейса к AI-агенту

Агент помогает элитным пассажирам с:
- Изменением мест в самолёте
- Отменой и изменением бронирований
- Управлением багажом
- Специальными запросами

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                       Frontend (React)                      │
│                     ChatKit Panel + UI                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/JSON
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Serverless Container (ChatKit Agent)           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (chatkit_server.py)                  │   │
│  │  - POST /support/chatkit - запросы к chatkit-серверу │   │
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
│  │  YDB Document API Store (store.py)                   │   │
│  │  - Threads (чаты)                                    │   │
│  │  - Messages (сообщения)                              │   │
│  │  - Attachments (вложения)                            │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                             │
│               │  ┌────────────────────────────────────┐     │
│               └──▶ Yandex IAM (yandex_iam.py)         │     │
│                  │ - Автоматическое получение токенов │     │
│                  │ - Подпись запросов Bearer токеном  │     │
│                  └─────────────┬──────────────────────┘     │
└────────────────────────────────┼────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌────────────────┐   ┌──────────────────┐   ┌─────────────────┐
│  YDB Document  │   │  Responses API   │   │   MCP Server    │
│      API       │   │   (YandexGPT)    │   │  (Airline API)  │
│  (Serverless)  │   │                  │   │                 │
└────────────────┘   └──────────────────┘   └─────────────────┘
```

### Компоненты

1. **FastAPI Server** - HTTP API для взаимодействия с фронтендом
2. **Customer Support Agent** - Логика агента на основе AI Studio Responses API
3. **YDB Document API Store** - Хранение истории чатов в YDB Document API
4. **Yandex IAM** - Автоматическая авторизация через IAM токены
5. **Airline Client** - Интеграция с API авиакомпании через AI Studio MCP Hub

## ⚡ Быстрый старт

Для быстрого развертывания выполните следующие команды:

```bash
# 1. Настройка переменных
export FOLDER_ID=$(yc config get folder-id)
export REGISTRY_NAME="my-registry"
export SA_NAME="chatkit-sa"

# 2. Сборка и загрузка образа
cd chatkit-agent
docker build -t chatkit-agent:latest .
yc container registry create --name ${REGISTRY_NAME}
REGISTRY_ID=$(yc container registry get --name ${REGISTRY_NAME} --format json | jq -r '.id')
docker tag chatkit-agent:latest cr.yandex/${REGISTRY_ID}/chatkit-agent:latest
yc container registry configure-docker
docker push cr.yandex/${REGISTRY_ID}/chatkit-agent:latest

# 3. Создание инфраструктуры
yc ydb database create --name chatkit-db --serverless
DOCUMENT_API_ENDPOINT=$(yc ydb database get chatkit-db --format json | jq -r '.document_api_endpoint')

# 4. Настройка сервисного аккаунта и API-ключа
yc iam service-account create --name ${SA_NAME}
SA_ID=$(yc iam service-account get ${SA_NAME} --format json | jq -r '.id')

# Назначение ролей
for role in lockbox.payloadViewer container-registry.images.puller serverless.containers.invoker \
            serverless.mcpGateways.invoker ai.assistants.editor ai.languageModels.user ydb.editor; do
  yc resourcemanager folder add-access-binding ${FOLDER_ID} --role ${role} --subject serviceAccount:${SA_ID}
done

# Создание API-ключа и секрета
yc iam api-key create --service-account-id ${SA_ID} \
  --scope "yc.ai.languageModels.execute" \
  --scope "yc.serverless.containers.invoke" \
  --scope "yc.serverless.mcpGateways.invoke" \
  --format json > api-key.json
API_KEY=$(cat api-key.json | jq -r '.secret')
yc lockbox secret create --name chatkit-api-key --payload "[{'key': 'API_KEY', 'text_value': '${API_KEY}'}]"
SECRET_ID=$(yc lockbox secret get chatkit-api-key --format json | jq -r '.id')

# 5. Деплой контейнера
yc serverless container create --name chatkit-agent
yc serverless container revision deploy \
  --container-name chatkit-agent \
  --image cr.yandex/${REGISTRY_ID}/chatkit-agent:latest \
  --service-account-id ${SA_ID} \
  --memory 1GB --cores 1 --execution-timeout 60s --concurrency 4 \
  --environment FOLDER_ID=${FOLDER_ID} \
  --environment USE_MEMORY_STORE=false \
  --environment AWS_REGION=ru-central1 \
  --environment DYNAMODB_ENDPOINT_URL=${DOCUMENT_API_ENDPOINT} \
  --environment DYNAMODB_TABLE_PREFIX=chatkit \
  --environment AUTO_CREATE_TABLES=true \
  --secret environment-variable=API_KEY,id=${SECRET_ID},version-id=latest,key=API_KEY

yc serverless container allow-unauthenticated-invoke chatkit-agent

# 6. Получить URL
echo "Container URL: $(yc serverless container get chatkit-agent --format json | jq -r '.url')"
```

> **Примечание**: Эта команда создает базовую конфигурацию без MCP сервера и векторного поиска. См. подробную инструкцию ниже для полной настройки.

## 🚀 Развертывание в Yandex Cloud (подробная инструкция)

Эта инструкция описывает полный процесс развертывания ChatKit агента в Yandex Cloud Serverless Containers со всеми компонентами.

### Предварительные требования

- Установленный [Yandex Cloud CLI](https://cloud.yandex.ru/docs/cli/quickstart)
- Docker для сборки образа
- Права на создание ресурсов в Yandex Cloud

### Шаг 1: Сборка Docker-образа

Соберите Docker-образ агента:

```bash
cd chatkit-agent

# Сборка образа
docker build -t chatkit-agent:latest .
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
docker tag chatkit-agent:latest cr.yandex/${REGISTRY_ID}/chatkit-agent:latest

# Загрузка образа
docker push cr.yandex/${REGISTRY_ID}/chatkit-agent:latest
```

### Шаг 3: Создание базы данных YDB Document API

Создайте Serverless YDB базу данных с поддержкой Document API:

```bash
# Создание Serverless YDB
yc ydb database create \
  --name chatkit-db \
  --serverless

# Получение Document API endpoint
DOCUMENT_API_ENDPOINT=$(yc ydb database get chatkit-db --format json | jq -r '.document_api_endpoint')

echo "Document API Endpoint: ${DOCUMENT_API_ENDPOINT}"
```

> **Примечание**: Сохраните значение `DOCUMENT_API_ENDPOINT` - оно понадобится для настройки переменных окружения.

### Шаг 4: Создание сервисного аккаунта с ролями

Создайте сервисный аккаунт и назначьте ему необходимые роли:

```bash
# Создание сервисного аккаунта
yc iam service-account create --name chatkit-sa --description "Service account for ChatKit agent"

# Получение ID сервисного аккаунта
SA_ID=$(yc iam service-account get chatkit-sa --format json | jq -r '.id')

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

yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role serverless.mcpGateways.invoker \
  --subject serviceAccount:${SA_ID}

yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role ai.assistants.editor \
  --subject serviceAccount:${SA_ID}

yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role ai.languageModels.user \
  --subject serviceAccount:${SA_ID}

yc resourcemanager folder add-access-binding ${FOLDER_ID} \
  --role ydb.editor \
  --subject serviceAccount:${SA_ID}
```

### Шаг 5: Создание API-ключа с необходимыми скоупами

Создайте API-ключ для сервисного аккаунта с необходимыми правами:

```bash
# Создание API-ключа со скоупами
yc iam api-key create \
  --service-account-id ${SA_ID} \
  --description "API key for ChatKit agent" \
  --scope "yc.ai.languageModels.execute" \
  --scope "yc.serverless.containers.invoke" \
  --scope "yc.serverless.mcpGateways.invoke" \
  --format json > api-key.json

# Извлечение секретного ключа
API_KEY=$(cat api-key.json | jq -r '.secret')

echo "API Key: ${API_KEY}"
```

> **Важно**: Сохраните `API_KEY` в безопасном месте. Он будет нужен для создания секрета Lockbox.

### Шаг 6: Создание секрета Lockbox

Создайте секрет в Yandex Lockbox для хранения API-ключа:

```bash
# Создание секрета с API-ключом
yc lockbox secret create \
  --name chatkit-api-key \
  --description "API key for ChatKit agent" \
  --payload "[{'key': 'API_KEY', 'text_value': '${API_KEY}'}]"

# Получение ID секрета
SECRET_ID=$(yc lockbox secret get chatkit-api-key --format json | jq -r '.id')

echo "Secret ID: ${SECRET_ID}"
```

### Шаг 7: Создание Serverless Container и деплой

Создайте публичный Serverless Container и разверните ревизию:

```bash
# Создание контейнера
yc serverless container create --name chatkit-agent

# Получение URL airline-api (если используется)
# Замените на актуальный URL вашего MCP сервера
AIRLINE_API_URL="https://your-airline-api-url.com"

# Создание векторного хранилища (опционально)
# Если не используется File Search, оставьте VECTOR_STORE_ID пустым
VECTOR_STORE_ID=""

# Деплой ревизии контейнера
yc serverless container revision deploy \
  --container-name chatkit-agent \
  --image cr.yandex/${REGISTRY_ID}/chatkit-agent:latest \
  --service-account-id ${SA_ID} \
  --memory 1GB \
  --cores 1 \
  --execution-timeout 60s \
  --concurrency 4 \
  --environment FOLDER_ID=${FOLDER_ID} \
  --environment USE_MEMORY_STORE=false \
  --environment AWS_REGION=ru-central1 \
  --environment DYNAMODB_ENDPOINT_URL=${DOCUMENT_API_ENDPOINT} \
  --environment DYNAMODB_TABLE_PREFIX=chatkit \
  --environment AUTO_CREATE_TABLES=true \
  --environment AIRLINE_API_URL=${AIRLINE_API_URL} \
  --environment VECTOR_STORE_ID=${VECTOR_STORE_ID} \
  --secret environment-variable=API_KEY,id=${SECRET_ID},version-id=latest,key=API_KEY

# Сделать контейнер публичным
yc serverless container allow-unauthenticated-invoke chatkit-agent

# Получить URL контейнера
CONTAINER_URL=$(yc serverless container get chatkit-agent --format json | jq -r '.url')

echo "Container URL: ${CONTAINER_URL}"
```

### Проверка развертывания

Проверьте, что агент работает корректно:

```bash
# Проверка health endpoint (если есть)
curl ${CONTAINER_URL}/

# Получение списка чатов
curl ${CONTAINER_URL}/threads

# Создание нового чата
curl -X POST ${CONTAINER_URL}/invoke \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, I need help with my flight",
    "context_id": "customer123"
  }'
```

## 📝 Переменные окружения

Полный список переменных окружения для Serverless Container:

| Переменная | Обязательная | Описание |
|------------|--------------|----------|
| `PORT` | Да | Порт для HTTP сервера (обычно 8000) |
| `API_KEY` | Да | API-ключ Yandex Cloud (из Lockbox) |
| `FOLDER_ID` | Да | ID каталога Yandex Cloud |
| `USE_MEMORY_STORE` | Да | `false` для использования DynamoDB |
| `AWS_REGION` | Да | `ru-central1` для Yandex Cloud |
| `DYNAMODB_ENDPOINT_URL` | Да | URL Document API endpoint |
| `DYNAMODB_TABLE_PREFIX` | Нет | Префикс для таблиц (по умолчанию `chatkit`) |
| `AUTO_CREATE_TABLES` | Нет | Автоматическое создание таблиц (`true`) |
| `AIRLINE_API_URL` | Нет | URL MCP сервера Airline API |
| `VECTOR_STORE_ID` | Нет | ID векторного хранилища для File Search |
| `MCP_SERVER_URL` | Нет | URL дополнительного MCP сервера |

## 📚 Полезные ссылки

### Документация Yandex Cloud
- [YDB Document API](https://cloud.yandex.ru/docs/ydb/docapi/)
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

### Документация OpenAI
- [OpenAI Agents SDK](https://openai.github.io/openai-agents-python)
- [OpenAI ChatKit](https://platform.openai.com/docs/guides/chatkit)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте логи контейнера: `yc serverless container revision logs <REVISION_ID>`
2. Убедитесь, что все переменные окружения заданы правильно
3. Проверьте доступность MCP сервера и Airline API
4. Убедитесь, что сервисный аккаунт имеет все необходимые роли
