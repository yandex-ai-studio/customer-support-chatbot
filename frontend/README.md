# Customer Support Frontend

Современный веб-интерфейс для системы поддержки клиентов авиакомпании с интеграцией OpenAI ChatKit.

## 📖 Содержание

- [Описание](#-описание)
- [Архитектура](#️-архитектура)
- [Технологический стек](#-технологический-стек)
- [Быстрый старт](#-быстрый-старт)
- [Разработка](#-разработка)
- [Конфигурация](#-конфигурация)
- [Компоненты](#-компоненты)
- [Развертывание](#-развертывание)
- [Переменные окружения](#-переменные-окружения)
- [Устранение неполадок](#-устранение-неполадок)
- [Полезные ссылки](#-полезные-ссылки)

## 📋 Описание

Customer Support Frontend — это React приложение, предоставляющее интерфейс для агентов службы поддержки авиакомпании. Приложение объединяет:

- **ChatKit панель** - интерактивный чат с AI агентом для обработки запросов клиентов
- **Панель контекста клиента** - динамическое отображение профиля, маршрутов и истории взаимодействий
- **Тёмная/светлая тема** - переключение цветовых схем для комфортной работы
- **Адаптивный дизайн** - оптимизирован для desktop и планшетов

### Основные возможности

✨ **Интерактивный чат**
- Интеграция OpenAI ChatKit для естественных диалогов
- Стартовые подсказки для быстрого начала
- Потоковая передача ответов (streaming)

👤 **Контекст клиента**
- Профиль с программой лояльности
- Предстоящие рейсы и маршруты
- История действий (timeline)
- Багаж, предпочтения питания, запросы на помощь

🎨 **Современный дизайн**
- Tailwind CSS для стилизации
- Glassmorphism эффекты
- Плавные анимации и переходы
- Темная и светлая темы

## 🏗️ Архитектура

```
┌────────────────────────────────────────────────────────────┐
│                       Browser                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │                App.tsx (Main)                         │ │
│  │  - useColorScheme() для управления темой              │ │
│  └─────────────────┬─────────────────────────────────────┘ │
│                    │                                       │
│  ┌─────────────────▼─────────────────────────────────────┐ │
│  │           Home.tsx (Layout)                           │ │
│  │  - Общий макет приложения                             │ │
│  │  - Управление состоянием thread                       │ │
│  └──────┬──────────────────────────────┬─────────────────┘ │
│         │                              │                   │
│  ┌──────▼──────────────┐      ┌────────▼────────────────┐  │
│  │  ChatKitPanel.tsx   │      │ CustomerContextPanel    │  │
│  │  ┌──────────────┐   │      │        .tsx             │  │
│  │  │   ChatKit    │   │      │  ┌──────────────────┐   │  │
│  │  │  Component   │   │      │  │ Profile Header   │   │  │
│  │  └──────────────┘   │      │  │ Flight Segments  │   │  │
│  │  - useChatKit()     │      │  │ Bags/Meal/Help   │   │  │
│  │  - Theme config     │      │  │ Timeline         │   │  │
│  │  - Event handlers   │      │  │ Tier Benefits    │   │  │
│  └──────┬──────────────┘      │  └──────────────────┘   │  │
│         │                     │  - useCustomerContext() │  │
│         │                     └────────┬────────────────┘  │
│         │                              │                   │
└─────────┼──────────────────────────────┼───────────────────┘
          │                              │
          │ POST /support/chatkit        │ GET /support/profile/{id}
          ▼                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Vite Dev Server (localhost:5171)                │
│                      Proxy: /support/*                       │
│                            ↓                                 │
│              Backend: http://localhost:8000/support/*        │
└─────────────────────────────────────────────────────────────┘
          │                              │
          ▼                              ▼
┌─────────────────────┐     ┌───────────────────────┐
│  ChatKit Agent      │     │   Airline API         │
│  (port 8000)        │     │   (через proxy)       │
│  - POST /chatkit    │     │   - GET /profile/{id} │
└─────────────────────┘     └───────────────────────┘
```

### Основные компоненты

1. **App.tsx** - Корневой компонент с управлением темой
2. **Home.tsx** - Основной layout с двухпанельной структурой
3. **ChatKitPanel.tsx** - Интеграция OpenAI ChatKit
4. **CustomerContextPanel.tsx** - Отображение данных клиента
5. **ThemeToggle.tsx** - Переключатель темной/светлой темы

### Хуки

- **useColorScheme** - Управление темой (dark/light) с сохранением в localStorage
- **useCustomerContext** - Загрузка и обновление профиля клиента

### Поток данных

1. Пользователь отправляет сообщение в ChatKit
2. ChatKit вызывает `/support/chatkit` (проксируется в chatkit-agent)
3. Агент обрабатывает запрос и возвращает ответ (streaming)
4. При завершении ответа вызывается `onResponseCompleted()`
5. Frontend обновляет контекст клиента через `/support/profile/{id}`
6. CustomerContextPanel отображает обновленные данные

## 💻 Технологический стек

### Основные технологии

- **[React 19](https://react.dev/)** - UI библиотека
- **[TypeScript](https://www.typescriptlang.org/)** - Типизация
- **[Vite](https://vitejs.dev/)** - Сборщик и dev-сервер
- **[Tailwind CSS](https://tailwindcss.com/)** - CSS фреймворк

### Библиотеки

- **[@openai/chatkit-react](https://platform.openai.com/docs/guides/chatkit)** - ChatKit компонент
- **[Lucide React](https://lucide.dev/)** - Иконки
- **[clsx](https://github.com/lukeed/clsx)** - Утилита для классов

### Dev инструменты

- **[ESLint](https://eslint.org/)** - Линтинг кода
- **[Vitest](https://vitest.dev/)** - Тестирование
- **[PostCSS](https://postcss.org/)** - CSS обработка
- **[Autoprefixer](https://autoprefixer.github.io/)** - CSS префиксы

## ⚡ Быстрый старт

### Предварительные требования

- Node.js 18.18 или выше
- npm 9 или выше
- Запущенный chatkit-agent (порт 8000)

### Установка и запуск

```bash
# 1. Перейдите в директорию frontend
cd frontend

# 2. Установите зависимости
npm install

# 3. Запустите dev-сервер
npm run dev

# Приложение будет доступно по адресу http://localhost:5171
```

## 🛠️ Разработка

### Доступные скрипты

```bash
# Запуск dev-сервера с hot reload
npm run dev

# Сборка production версии
npm run build

# Предварительный просмотр production сборки
npm run preview

# Линтинг кода
npm run lint
```

### Структура проекта

```
frontend/
├── src/
│   ├── components/           # React компоненты
│   │   ├── ChatKitPanel.tsx  # Панель чата
│   │   ├── CustomerContextPanel.tsx  # Контекст клиента
│   │   ├── Home.tsx          # Главный layout
│   │   └── ThemeToggle.tsx   # Переключатель темы
│   ├── hooks/                # Пользовательские хуки
│   │   ├── useColorScheme.ts # Управление темой
│   │   └── useCustomerContext.ts # Загрузка профилей
│   ├── lib/
│   │   └── config.ts         # Конфигурация приложения
│   ├── App.tsx               # Корневой компонент
│   ├── main.tsx              # Точка входа
│   └── index.css             # Глобальные стили
├── public/                   # Статические файлы
├── index.html                # HTML шаблон
├── vite.config.ts            # Конфигурация Vite
├── tailwind.config.ts        # Конфигурация Tailwind
├── tsconfig.json             # Конфигурация TypeScript
└── package.json              # Зависимости
```

### Стилизация

Приложение использует **Tailwind CSS** с кастомными утилитами:

```tsx
// Примеры использования
<div className="rounded-3xl bg-white/80 shadow-[0_45px_90px_-45px_rgba(15,23,42,0.6)] backdrop-blur">
  // Glassmorphism эффект
</div>

<div className="dark:bg-slate-900 dark:text-slate-100">
  // Поддержка темной темы
</div>
```

### Добавление новых компонентов

```tsx
// src/components/MyComponent.tsx
import { useState } from "react";

type MyComponentProps = {
  title: string;
};

export function MyComponent({ title }: MyComponentProps) {
  const [count, setCount] = useState(0);

  return (
    <div className="rounded-xl bg-white p-4 dark:bg-slate-900">
      <h3 className="text-lg font-semibold">{title}</h3>
      <button
        onClick={() => setCount(count + 1)}
        className="mt-2 rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
      >
        Count: {count}
      </button>
    </div>
  );
}
```

## ⚙️ Конфигурация

### Переменные окружения

Создайте файл `.env.local` в корне frontend директории:

```bash
# Backend API (chatkit-agent)
VITE_SUPPORT_API_BASE=http://localhost:8000/support

# ChatKit Domain Key (для production)
VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY=domain_pk_your_key

# Кастомное приветствие (опционально)
VITE_SUPPORT_GREETING="Welcome to Airline Support!"

# URL для получения профилей из Airline API (если отличается)
VITE_SUPPORT_CUSTOMER_URL=http://localhost:8000/support/profile
```

### Vite конфигурация

**vite.config.ts** настроен для проксирования запросов:

```typescript
export default defineConfig({
  server: {
    port: 5171,
    proxy: {
      "/support": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
```

Это позволяет избежать проблем с CORS в разработке.

### Tailwind конфигурация

**tailwind.config.ts** настроен для темной темы:

```typescript
export default {
  darkMode: "class", // Управление через класс
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  // ... остальная конфигурация
}
```

## 🎨 Компоненты

### ChatKitPanel

Компонент интеграции OpenAI ChatKit:

```tsx
<ChatKitPanel
  theme={scheme} // "dark" | "light"
  onThreadChange={(threadId) => {
    // Вызывается при смене чата
  }}
  onResponseCompleted={() => {
    // Вызывается после завершения ответа
  }}
/>
```

**Особенности:**
- Конфигурируемая цветовая схема
- Стартовые подсказки
- Streaming ответов
- Обработка ошибок

### CustomerContextPanel

Панель отображения профиля клиента:

```tsx
<CustomerContextPanel
  profile={profile} // CustomerProfile | null
  loading={loading} // boolean
  error={error}     // string | null
/>
```

**Отображаемая информация:**
- Имя и статус лояльности
- Email и телефон
- Предстоящие рейсы (origin, destination, seat, status)
- Багаж и предпочтения питания
- Timeline действий агента
- Привилегии программы лояльности

### ThemeToggle

Переключатель темной/светлой темы:

```tsx
<ThemeToggle
  value={scheme}           // "dark" | "light"
  onChange={setScheme}     // (scheme: ColorScheme) => void
/>
```

### Пользовательские хуки

#### useColorScheme

```typescript
const { scheme, setScheme } = useColorScheme();

// scheme: "dark" | "light"
// setScheme: (scheme: ColorScheme) => void
// Автоматически сохраняет в localStorage
```

#### useCustomerContext

```typescript
const { profile, loading, error, refresh } = useCustomerContext(threadId);

// profile: CustomerProfile | null
// loading: boolean
// error: string | null
// refresh: () => Promise<void>
```

## 🚀 Развертывание

### Развертывание в Yandex Cloud Object Storage

Рекомендуемый способ развертывания frontend — использование Yandex Cloud Object Storage с функцией веб-хостинга.

#### Предварительные требования

- Установленный [Yandex Cloud CLI](https://cloud.yandex.ru/docs/cli/quickstart)
- Развернутый chatkit-agent в Yandex Cloud Serverless Containers (см. [../chatkit-agent/README.md](../chatkit-agent/README.md))
- Node.js 18+ и npm

#### Шаг 1: Создание бакета в Object Storage

Создайте бакет для хостинга статических файлов:

```bash
# Создайте бакет с уникальным именем
BUCKET_NAME="customer-support-frontend"
yc storage bucket create --name ${BUCKET_NAME}

# Настройте публичный доступ для чтения
yc storage bucket update --name ${BUCKET_NAME} --public-read

# Настройте веб-хостинг
yc storage bucket update --name ${BUCKET_NAME} \
  --website-settings '{
    "index": "index.html",
    "error": "index.html"
  }'

# Получите URL бакета
BUCKET_URL="${BUCKET_NAME}.website.yandexcloud.net"
echo "Frontend URL: https://${BUCKET_URL}"
```

> **Примечание**: Для собственного домена настройте CNAME запись в DNS, указывающую на `${BUCKET_NAME}.website.yandexcloud.net`.

#### Шаг 2: Регистрация домена в OpenAI Platform

Зарегистрируйте домен для получения Domain Key:

1. Откройте [Domain Allowlist](https://platform.openai.com/settings/organization/security/domain-allowlist)
2. Нажмите **Add domain**
3. Введите ваш домен:
   - Для бакета: `${BUCKET_NAME}.website.yandexcloud.net`
   - Для своего домена: `your-domain.com`
4. Скопируйте **Domain Key** (формат: `domain_pk_...`)

#### Шаг 3: Настройка переменных окружения

Создайте `.env.production` с production настройками:

```bash
# В директории frontend/
cat > .env.production << EOF
# URL развернутого chatkit-agent в Yandex Cloud
VITE_SUPPORT_API_BASE=https://your-chatkit-agent-id.containers.yandexcloud.net/support

# Domain Key из OpenAI Platform
VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY=domain_pk_your_production_key

# URL для получения профилей (через chatkit-agent)
VITE_SUPPORT_CUSTOMER_URL=https://your-chatkit-agent-id.containers.yandexcloud.net/support/profile

# Опционально: кастомное приветствие
VITE_SUPPORT_GREETING="Thanks for reaching our airline concierge. How can I make your trip smoother today?"
EOF
```

> **Важно**: Замените `your-chatkit-agent-id.containers.yandexcloud.net` на реальный URL вашего chatkit-agent контейнера.

Получить URL chatkit-agent:

```bash
yc serverless container get chatkit-agent --format json | jq -r '.url'
```

#### Шаг 4: Сборка проекта

Соберите production версию:

```bash
# Убедитесь, что вы в директории frontend/
cd frontend

# Установите зависимости
npm install

# Соберите production версию
npm run build

# Проверьте результат
ls -la dist/
```

Production сборка включает:
- ✅ Минифицированные JavaScript и CSS
- ✅ Оптимизированные изображения
- ✅ Source maps для отладки
- ✅ Все переменные из `.env.production`

#### Шаг 5: Загрузка файлов в бакет

**Вариант 1: Через AWS CLI (рекомендуется)**

```bash
# Установите AWS CLI
# macOS: brew install awscli
# Ubuntu: sudo apt install awscli

# Настройте credentials для Yandex Cloud
aws configure set aws_access_key_id <your_access_key_id>
aws configure set aws_secret_access_key <your_secret_key>

# Загрузите все файлы рекурсивно
aws s3 sync dist/ s3://${BUCKET_NAME}/ \
  --endpoint-url=https://storage.yandexcloud.net \
  --acl public-read
```

**Вариант 2: Через Yandex Cloud CLI**

```bash
# Скрипт для загрузки всех файлов с правильными Content-Type
cd dist
find . -type f | while read file; do
  key="${file#./}"
  
  # Определение Content-Type
  case "$file" in
    *.html) content_type="text/html" ;;
    *.css) content_type="text/css" ;;
    *.js) content_type="application/javascript" ;;
    *.json) content_type="application/json" ;;
    *.png) content_type="image/png" ;;
    *.jpg|*.jpeg) content_type="image/jpeg" ;;
    *.svg) content_type="image/svg+xml" ;;
    *.ico) content_type="image/x-icon" ;;
    *) content_type="application/octet-stream" ;;
  esac
  
  yc storage s3api put-object \
    --bucket ${BUCKET_NAME} \
    --key "$key" \
    --body "$file" \
    --content-type "$content_type" \
    --acl public-read
done
cd ..
```

**Вариант 3: Через веб-консоль**

1. Откройте [Yandex Cloud Console](https://console.cloud.yandex.ru/)
2. Object Storage → Ваш бакет
3. Нажмите **Загрузить** → выберите все файлы из `dist/`

#### Проверка развертывания

После загрузки проверьте работу:

```bash
# Откройте в браузере
echo "Frontend: https://${BUCKET_URL}"

# Проверьте доступность
curl -I https://${BUCKET_URL}
```

**Чеклист проверки:**
- ✅ Frontend загружается корректно
- ✅ ChatKit панель подключается к backend
- ✅ Профили клиентов загружаются
- ✅ Агент отвечает на запросы
- ✅ Timeline обновляется после действий
- ✅ Тема (dark/light) переключается и сохраняется

#### Обновление приложения

Для обновления после изменений:

```bash
# 1. Внесите изменения в код
# 2. Пересоберите
npm run build

# 3. Загрузите обновленные файлы
aws s3 sync dist/ s3://${BUCKET_NAME}/ \
  --endpoint-url=https://storage.yandexcloud.net \
  --acl public-read \
  --delete  # Удалит старые файлы

# 4. Очистите кеш браузера (Ctrl+Shift+R / Cmd+Shift+R)
```

#### Настройка CORS (если требуется)

Если chatkit-agent на другом домене, настройте CORS:

```bash
yc storage bucket update --name ${BUCKET_NAME} \
  --cors '[
    {
      "id": "allow-chatkit",
      "allowed_methods": ["GET", "POST", "PUT", "DELETE", "HEAD"],
      "allowed_origins": ["https://your-chatkit-agent-id.containers.yandexcloud.net"],
      "allowed_headers": ["*"],
      "max_age_seconds": 3600
    }
  ]'
```

## 📝 Переменные окружения

| Переменная | По умолчанию | Описание |
|------------|--------------|----------|
| `VITE_SUPPORT_API_BASE` | `/support` | Base URL для API запросов |
| `VITE_SUPPORT_CHATKIT_API_URL` | `${BASE}/chatkit` | URL ChatKit endpoint |
| `VITE_SUPPORT_CUSTOMER_URL` | `${BASE}/profile` | URL для получения профилей |
| `VITE_SUPPORT_CHATKIT_API_DOMAIN_KEY` | `domain_pk_localhost_dev` | ChatKit domain key |
| `VITE_SUPPORT_GREETING` | *airline greeting* | Приветственное сообщение |
| `BACKEND_URL` | `http://127.0.0.1:8000` | Backend URL для Vite proxy |

## 🔧 Устранение неполадок

### ChatKit не загружается

**Проблема:** ChatKit компонент не отображается или показывает ошибку.

**Решение:**
1. Проверьте, что chatkit-agent запущен на порту 8000
2. Убедитесь, что `VITE_SUPPORT_API_BASE` настроен правильно
3. Проверьте консоль браузера на наличие ошибок CORS
4. Убедитесь, что domain key валиден (для production)

```bash
# Проверка доступности backend
curl http://localhost:8000/support/chatkit
```

### Профиль клиента не загружается

**Проблема:** CustomerContextPanel показывает "Loading..." или ошибку.

**Решение:**
1. Проверьте Network tab в DevTools
2. Убедитесь, что endpoint `/support/profile/{id}` доступен
3. Проверьте CORS настройки в chatkit-agent

```bash
# Проверка endpoint
curl http://localhost:8000/support/profile/demo_default_thread
```

### CORS ошибки в production

**Проблема:** Browser блокирует запросы из-за CORS.

**Решение:**
1. Убедитесь, что frontend и backend на одном домене
2. Или настройте CORS в chatkit-agent:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Стили не применяются

**Проблема:** Tailwind классы не работают.

**Решение:**
1. Проверьте `tailwind.config.ts` content paths
2. Убедитесь, что PostCSS настроен правильно
3. Перезапустите dev-сервер

```bash
# Очистка кеша и перезапуск
rm -rf node_modules/.vite
npm run dev
```

### Theme не сохраняется

**Проблема:** После перезагрузки страницы тема сбрасывается.

**Решение:**
1. Проверьте localStorage в DevTools
2. Убедитесь, что `THEME_STORAGE_KEY` уникален
3. Проверьте console на ошибки

```javascript
// В консоли браузера
localStorage.getItem('customer-support-theme')
```

## 📊 Производительность

### Оптимизации в production сборке

- ✅ Минификация JavaScript и CSS
- ✅ Tree-shaking неиспользуемого кода
- ✅ Code splitting для оптимизации загрузки
- ✅ Сжатие изображений и ассетов
- ✅ Prefetching критических ресурсов

### Рекомендации

1. **Lazy loading компонентов:**
```typescript
const CustomerContextPanel = lazy(() => 
  import('./components/CustomerContextPanel')
);
```

2. **Мemoization:**
```typescript
const MemoizedPanel = memo(CustomerContextPanel);
```

3. **Виртуализация длинных списков:**
```typescript
// Для больших timeline списков
import { VirtualList } from 'react-window';
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Запуск Vitest
npm run test

# С coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Пример теста

```typescript
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ThemeToggle } from './ThemeToggle';

describe('ThemeToggle', () => {
  it('renders theme toggle button', () => {
    render(<ThemeToggle value="light" onChange={() => {}} />);
    expect(screen.getByRole('button')).toBeInTheDocument();
  });
});
```

## 📚 Полезные ссылки

### Документация

- [React Documentation](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Vite Guide](https://vitejs.dev/guide/)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [OpenAI ChatKit Documentation](https://platform.openai.com/docs/guides/chatkit)

### Инструменты

- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Tailwind CSS IntelliSense](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)
- [ES7+ React/Redux/React-Native snippets](https://marketplace.visualstudio.com/items?itemName=dsznajder.es7-react-js-snippets)

### Библиотеки

- [Lucide Icons](https://lucide.dev/icons/)
- [clsx utility](https://github.com/lukeed/clsx)

## 🤝 Поддержка

При возникновении проблем:
1. Проверьте консоль браузера (F12)
2. Проверьте Network tab для API запросов
3. Убедитесь, что backend (chatkit-agent) запущен
4. Проверьте переменные окружения
5. Очистите кеш браузера и node_modules/.vite

---

**Совет:** Используйте React DevTools для отладки состояния компонентов и Chrome DevTools Network tab для анализа API запросов.

