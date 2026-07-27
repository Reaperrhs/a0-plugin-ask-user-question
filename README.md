# 🙋 Ask User Question — Agent Zero Plugin

[![Version](https://img.shields.io/badge/version-1.0.2-blue.svg)](https://github.com/Reaperrhs/a0-plugin-ask-user-question)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Agent Zero](https://img.shields.io/badge/Agent%20Zero-Plugin-purple.svg)](https://github.com/agent0ai/agent-zero)

**Lets AI agents ask structured clarifying questions with a beautiful tabbed modal UI.**

Instead of guessing what the user wants, the agent presents clear options and lets the user choose — directly inside the Agent Zero web interface.

<!-- ![Screenshot](docs/screenshot.png) -->

---

## ✨ Features

- **Structured Questions** — Agent presents 1–4 questions, each with 2–4 predefined options
- **Tabbed Modal UI** — Clean, animated tabbed interface that fits the Agent Zero dark theme
- **Markdown Previews** — Options can include markdown preview panes for rich context
- **Multi-Select Support** — Allow users to pick multiple options per question
- **Free-Text "Other"** — Users can always type a custom answer beyond the provided options
- **Optional Notes** — Each question has a notes field for additional context
- **Review & Submit** — Final review tab shows all answers before submission
- **Non-Blocking** — The tool waits for user input without breaking the agent loop
- **Timeout Handling** — Configurable timeout (default 300s) with graceful fallback
- **Notification Integration** — Pushes a notification when questions are pending
- **Responsive Design** — Works on desktop and mobile viewports

---

## 🔄 How It Works

### Agent-Side

1. The agent calls the `ask_user_question` tool with a JSON payload of questions
2. The tool creates a pending session and fires a notification
3. It blocks (async) until the user answers or the timeout expires
4. The structured answers are returned to the agent as a formatted message

### User-Side

1. The frontend polls for pending questions every 2 seconds
2. When a question is detected, a modal appears with tabbed questions
3. The user selects options, adds notes, and submits
4. The answer is sent to the backend API, which signals the waiting tool

---

## 📦 Installation

### From Plugin Hub (Recommended)

In your Agent Zero instance, go to **Settings → Plugins → Browse** and search for "Ask User Question".

### Manual Installation

1. Clone this repository into your Agent Zero plugins directory:

```bash
cd /path/to/agent-zero/usr/plugins
git clone https://github.com/Reaperrhs/a0-plugin-ask-user-question.git ask_user_question
```

2. Restart Agent Zero (or reload plugins from settings).

3. The plugin auto-registers:
   - **Tool**: `ask_user_question` (available to the agent)
   - **API endpoints**: `/plugins/ask_user_question/get_pending` and `/plugins/ask_user_question/submit_answer`
   - **WebUI extension**: Modal component injected into the chat page

---

## 🚀 Usage

### Basic Example — Single Question

```json
{
  "questions": [
    {
      "question": "Which database would you like to use?",
      "header": "Database",
      "options": [
        { "label": "PostgreSQL", "description": "Robust relational database" },
        { "label": "MongoDB", "description": "Flexible document store" },
        { "label": "SQLite", "description": "Lightweight, file-based" }
      ]
    }
  ]
}
```

### Advanced Example — Multiple Questions with Previews

```json
{
  "questions": [
    {
      "question": "Which architecture style do you prefer?",
      "header": "Architecture",
      "options": [
        {
          "label": "Microservices",
          "description": "Distributed services with independent deployment",
          "preview": "## Microservices\n\n- Independent deploy\n- Service mesh\n- Event-driven"
        },
        {
          "label": "Modular Monolith",
          "description": "Single deployable with module boundaries"
        },
        {
          "label": "Serverless",
          "description": "Functions-as-a-service, auto-scaling"
        }
      ]
    },
    {
      "question": "What is the priority for this project?",
      "header": "Priority",
      "multiSelect": false,
      "options": [
        { "label": "Speed", "description": "Ship fast, iterate later" },
        { "label": "Quality", "description": "Production-grade from the start" },
        { "label": "Cost-efficient", "description": "Minimize infrastructure and dev time" }
      ]
    }
  ],
  "timeout": 120
}
```

### Tool Response

When the user answers, the agent receives:

```
User answered the following questions:

Q1: Which architecture style do you prefer?
  Selected: Microservices

Q2: What is the priority for this project?
  Selected: Speed
  Notes: We need MVP in 2 weeks
```

---

## 📋 Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `questions` | array | ✅ | — | 1–4 structured question objects |
| `timeout` | integer | ❌ | 300 | Seconds to wait for user response |

### Question Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | ✅ | Question text (must end with `?`) |
| `header` | string | ✅ | Tab label, max 16 characters |
| `options` | array | ✅ | 2–4 option objects |
| `multiSelect` | boolean | ❌ | Allow multiple selections (default: false) |

### Option Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `label` | string | ✅ | Display text (max 60 chars) |
| `description` | string | ❌ | Brief explanation |
| `preview` | string | ❌ | Markdown shown in a preview pane |

### Reserved Labels

These labels are auto-provided and cannot be used:
- `Other` — Always shown with a free-text input
- `Type something.`
- `Chat about this`
- `Next →`

---

## 🔌 API Reference

### GET/POST `/plugins/ask_user_question/get_pending`

Check if there are pending questions for a context.

**Parameters:**
- `context_id` (string, required) — The chat context ID

**Response (pending):**
```json
{
  "ok": true,
  "pending": true,
  "session_id": "uuid",
  "questions": [...],
  "created_at": 1234567890.123
}
```

**Response (no pending):**
```json
{
  "ok": true,
  "pending": false
}
```

### POST `/plugins/ask_user_question/submit_answer`

Submit answers or cancel a pending session.

**Parameters:**
- `session_id` (string, required) — The session ID from `get_pending`
- `answers` (array, required unless cancelled) — Array of answer objects
- `cancelled` (boolean) — Set to `true` to decline answering

**Answer Object:**
```json
{
  "question_index": 0,
  "selected": ["Option Label"],
  "other_text": "",
  "notes": ""
}
```

**Response:**
```json
{ "ok": true }
```

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Agent Zero Framework                      │
│                                                              │
│  ┌─────────────────┐         ┌────────────────────────────┐ │
│  │   Agent (LLM)   │────────▶│  tools/ask_user_question   │ │
│  │                 │         │  - Validates questions      │ │
│  │                 │◀────────│  - Creates session          │ │
│  │                 │         │  - Waits on asyncio.Event   │ │
│  └─────────────────┘         └──────────┬─────────────────┘ │
│                                         │                    │
│                                         │ create_session()   │
│                                         ▼                    │
│  ┌──────────────────────────────────────────────────────────┐│
│  │               helpers/state.py (In-Memory)               ││
│  │  _pending: Dict[context_id → PendingSession]             ││
│  │  - create_session()  - submit_answer()                   ││
│  │  - get_pending()     - cancel_session()                  ││
│  │  - cleanup_old_sessions() (10min TTL)                    ││
│  └──────────┬──────────────────────────────▲────────────────┘│
│             │                              │                  │
│             │ API                          │ event.set()      │
│             ▼                              │                  │
│  ┌──────────────────────┐   ┌─────────────┴───────────────┐  │
│  │  api/get_pending.py  │   │  api/submit_answer.py       │  │
│  │  GET/POST            │   │  POST                       │  │
│  └──────────┬───────────┘   └─────────────────────────────┘  │
│             │                                                 │
└─────────────┼─────────────────────────────────────────────────┘
              │ HTTP
              ▼
┌──────────────────────────────────────────────────────────────┐
│                    WebUI (Browser)                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  webui/ask-store.js (Alpine.js Store)                    ││
│  │  - Polls /get_pending every 2s                           ││
│  │  - Manages modal state, answers, navigation              ││
│  └──────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │  extensions/webui/page-head/ask-question-setup.html      ││
│  │  - Injected into page <head>                              ││
│  │  - Contains CSS + Alpine.js modal template                ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

### State Management

- **In-Memory**: Sessions are stored in a Python dictionary, keyed by `context_id`
- **TTL**: Sessions expire after 10 minutes (`_MAX_AGE = 600`)
- **Supersession**: New questions for the same context cancel previous pending ones
- **Asyncio.Event**: The tool blocks on an `asyncio.Event` that is set when the user submits or cancels

### Frontend Polling

- The Alpine.js store polls `get_pending` every 2 seconds
- When a pending session is detected, the modal appears automatically
- After submission, the modal closes and polling resumes

---

## 🛠️ Development

### File Structure

```
ask_user_question/
├── plugin.yaml              # Plugin metadata
├── api/
│   ├── __init__.py
│   ├── get_pending.py       # GET/POST endpoint for pending questions
│   └── submit_answer.py     # POST endpoint for submitting answers
├── helpers/
│   ├── __init__.py
│   └── state.py             # In-memory session state management
├── tools/
│   ├── __init__.py
│   └── ask_user_question.py # Agent tool (async, blocking wait)
├── prompts/
│   └── agent.system.tool.ask_user_question.md  # Agent prompt instructions
├── extensions/
│   └── webui/
│       └── page-head/
│           └── ask-question-setup.html  # CSS + Alpine modal template
└── webui/
    └── ask-store.js         # Alpine.js reactive store
```

### Running Locally

1. Symlink or copy the plugin into your Agent Zero `usr/plugins/` directory
2. Restart Agent Zero
3. In a chat, the agent can invoke the tool when it needs clarification

### Modifying the UI

- **Styles**: Edit the `<style>` block in `extensions/webui/page-head/ask-question-setup.html`
- **Modal Template**: Edit the Alpine.js `x-data` template in the same file
- **Store Logic**: Edit `webui/ask-store.js` for polling, state, and API calls
- All CSS variables reference the Agent Zero theme (`--color-primary`, `--color-background-elevated`, etc.)

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

Copyright © 2025 Agent Zero Community
