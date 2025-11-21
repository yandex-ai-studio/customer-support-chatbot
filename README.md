# Customer Support ChatBot

## 📋 Описание

Customer Support ChatBot — это демонстрационное приложение, которое реализует чат-бот службы поддержки авиакомпании и использует сервисы Yandex AI Studio.

### ✨ Основные возможности

- 💬 Естественный диалог с AI ассистентом через ChatKit
- 👤 Автоматическая загрузка профиля клиента
- ✈️ Управление бронированиями и маршрутами
- 📋 История всех действий в реальном времени
- 🎨 Современный адаптивный интерфейс с темной темой

### ✨Технические возможности

- 🤖 AI-агент на базе Yandex AI Studio
- 🔌 MCP (Model Context Protocol) интеграция
- 📊 Векторный поиск по базе знаний
- 💾 Персистентное хранение в YDB Document API
- 🚀 Развертывание в Yandex AI Studio

## 🏗️ Архитектура

Проект состоит из четырех независимых микросервисов:

```
┌──────────────────────────┐              ┌─────────────────────────────┐
│  Browser (Пользователь)  │              │  Внешний агент / Сервис     │
│  ┌────────────────────┐  │              │  (например, другой AI)      │
│  │ Frontend (React)   │  │              └──────────────┬──────────────┘
│  │ + OpenAI ChatKit   │  │                             │
│  └────┬───────────┬───┘  │                             │ A2A Protocol
└───────┼───────────┼──────┘                             │ (HTTPS)
        │ HTTPS     │                                    │
        │           │ HTTPS (профили)                    │
        ▼           │                                    ▼
┌────────────────┐  │                         ┌──────────────────┐
│ ChatKit Agent  │  │                         │   A2A Agent      │
├────────────────┤  │                         ├──────────────────┤
│• ChatKit Server│  │                         │ • A2A Server     │
│• AI Agent      │  │                         │ • AI Agent       │
│• YDB Store     │  │                         │ • Task Store     │
│• MCP Client    │  │                         │ • MCP Client     │
└────────┬───────┘  │                         └────────┬─────────┘
         │          │                                  │
         │          │                                  │
         └──────────┼──────────┬───────────────────────┘
                    ▼          │
        ┌────────────────────┐ │       ┌────────────────────────┐
        │   Airline API      │◄┘       │  Yandex AI Studio      │
        │                    │◄────────│                        │
        ├────────────────────┤  MCP    ├────────────────────────┤
        │ • REST API         │         │ • YandexGPT            │
        │ • Profile CRUD     │         │ • Response API         │
        │ • YDB Store        │         │ • Vector Store API     │
        │ • MCP Server       │         │ • MCP Hub              │
        └────────────────────┘         └────────────────────────┘
```

## 📦 Компоненты проекта

### 1. [Frontend](./frontend/) - React + ChatKit UI

Современный веб-интерфейс для чатов с AI-агентами.

**Технологии:** React 19, TypeScript, Vite, Tailwind CSS, OpenAI ChatKit

**Возможности:**
- Интерактивная ChatKit панель для общения с AI-агентом
- Панель клиента с профилем и рейсами
- Темная/светлая тема с сохранением настроек
- Адаптивный дизайн для desktop и планшетов

**Развертывание:** Yandex Cloud Object Storage (веб-хостинг)

📖 **[Подробная документация →](./frontend/README.md)**

---

### 2. [ChatKit Agent](./chatkit-agent/) - AI-агент c ChatKit-сервером

FastAPI сервер с реализацией ChatKit-бекенда c AI-агентом на базе Yandex AI Studio.

**Технологии:** Python 3.11+, FastAPI, OpenAI Agents SDK, ChatKit, YDB Document API

**Возможности:**
- ChatKit сервер для обработки чатов
- AI-агент с YandexGPT моделью
- Интеграция с MCP сервером для инструментов
- Векторный поиск по базе знаний (File Search)
- Персистентное хранение в YDB Document API

**Развертывание:** Yandex Cloud Serverless Containers

📖 **[Подробная документация →](./chatkit-agent/README.md)**

---

### 4. [A2A Agent](./a2a-agent/) - AI-агент с поддержкой Agent-to-Agent протокола

Реализация AI-агента с поддержкой Agent-to-Agent (A2A) протокола для вызова другими агентами.

**Технологии:** Python 3.11+, A2A SDK, OpenAI Agents SDK, Yandex AI Studio

**Возможности:**
- Реализация A2A протокола (Agent Card, Skills)
- Stateless обработка задач (без хранения истории)
- Публичная Agent Card с описанием навыков
- Task-based workflow вместо threads

**Развертывание:** Yandex Cloud Serverless Containers

📖 **[Подробная документация →](./a2a-agent/README.md)**

---

### 3. [Airline API](./airline-api/) - REST API для работы с профилями клиентов

Микросервис для управления профилями клиентов и бронированиями.

**Технологии:** Python 3.11+, FastAPI, YDB Document API

**Возможности:**
- REST API для CRUD операций с профилями
- Управление рейсами и бронированиями
- Изменение мест, багажа, питания
- Timeline действий по каждому клиенту
- Интеграция с MCP Gateway для AI агентов

**Развертывание:** Yandex Cloud Serverless Containers + MCP Gateway

📖 **[Подробная документация →](./airline-api/README.md)**

---

## Развертывание в Yandex Cloud

1. **Airline API** → Serverless Container + MCP Gateway
2. **ChatKit Agent** → Serverless Container + YDB
3. **A2A Agent** → Serverless Container
4. **Frontend** → Object Storage (веб-хостинг)

Подробные инструкции по развертыванию в README каждого компонента.
