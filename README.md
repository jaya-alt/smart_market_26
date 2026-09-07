# smart_market_26 — Supermarket Ops Agent

## Overview

`smart_market_26` is an AI-powered supermarket operations agent that handles inventory, billing, customer khata, GST invoices, sales analysis, and store preferences through a Telegram-based conversational interface.

The application uses an LLM with tool calling. The agent understands the user's request and selects the appropriate business tool instead of using separate command-based flows for each operation.

**Telegram Bot:** smart_market_26_bot 

The bot is deployed and kept running for review.

---

## Harness & Control Loop

I used a **plain tool-calling agent loop** as the harness. This keeps the agent simple and allows the same conversation flow to handle different supermarket operations without building a separate workflow for every command.

The control loop works as follows:

```text
User Request
     ↓
LLM Agent
     ↓
Select required tool
     ↓
Execute tool
     ↓
Check tool result
     ↓
Continue if another tool is required
     ↓
Final response
```

For example, when creating a bill, the agent can search for the product, check stock, add the item to the draft bill, and then use the billing service to calculate the final amount.

The agent has a maximum iteration limit to prevent an unnecessary tool-calling loop.

---

## Skill / Tool Design

The tools are organized around supermarket operations rather than individual chat commands.

### Inventory

* Product search
* Stock lookup
* Receive stock
* Low-stock detection
* Reorder suggestions
* Stock movement tracking

### Billing

* Create draft bill
* Add bill items
* Edit bill items
* Remove bill items
* Get bill details
* Finalize bill
* GST calculation

### Customer Khata

* Find or create customer
* Check balance
* Add credit
* Record payment
* View customer ledger

### Reports & Documents

* Generate GST invoice PDF
* Generate sales analysis deck
* Generate daily closing report

### Preferences

* Set preference
* Get preference
* Retrieve stored preferences

The AI agent is responsible for deciding which tool is required, while the actual business rules are implemented inside the tools and services.

---

## Hard Parts & Solutions

### Overselling Prevention

Stock is checked before a bill item is added or a bill is finalized. If the requested quantity is greater than the available stock, the operation is rejected instead of allowing negative stock.

### Multi-item Billing & Editing

Bills are created as drafts. Items can be added, edited, or removed before finalization. The bill is recalculated after changes so that subtotal, GST, and total remain consistent.

### Khata Cycle

Customer credit and payments are stored as ledger transactions. The customer's balance is calculated from these transactions, allowing the full credit → balance → payment → updated balance cycle to be handled.

### Idempotency

Telegram updates are tracked so that the same update is not processed multiple times, reducing the chance of duplicate billing or other repeated operations.

### Persistence

Important business data such as products, stock, bills, customers, ledger transactions, and preferences are stored in the database so that information is available across conversations.

### Product Search

The agent searches the actual inventory and does not assume that a product exists. If a requested product is not present, it returns that the product was not found instead of inventing stock information.

### PDF Invoice & Analysis Deck

Completed bills can be converted into GST invoice PDFs, and sales data can be used to generate a PowerPoint analysis deck with charts.

### Preference Memory

Store preferences are persisted in the database. After setting a preference, starting a new `/new` chat does not remove the stored preference, so the agent can retrieve and use it again.

---

## Setup

Create a `.env` file using `.env.example` and configure the required credentials.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
DATABASE_URL=sqlite:///./supermarket.db
STORE_NAME=Sri Jaya Mart
AGENT_MAX_ITERATIONS=10
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize the database:

```bash
python init_db.py
```

Seed the sample products:

```bash
python -m app.database.seed
```

Start the Telegram bot:

```bash
python -m app.telegram.bot
```

The `.env` file and database files are excluded from Git using `.gitignore`.
