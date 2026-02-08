# btc-mcp

[https://devpost.com/software/btc-mcp](https://devpost.com/software/btc-mcp)

An online platform for creators to launch MCP servers and earn Bitcoin.

AI agents can interact with each other and exchange payments, with access and transactions powered by Lightspark/Bitcoin, including L402-style paywall semantics. Passwordless authentication via the LNURL protocol is used for verifying creators' identity. 

The platform uses MCP (FastMCP) to standardize agent and tool interfaces, enabling seamless agent-to-agent interactions. Redis manages caching and ephemeral state for Lightning authentication and Docker provides isolated, deployable environments for MCP servers.

Access the MCP network by simply connecting your Lightspark node to a Python client, allowing your agent to use tools and make automatic payments without human intervention. Creators earn for every input and output token processed by their server.

MCP servers can be vouched for by the community via staking.

# directory guide

## Root

```
btc-mcp/
├── README.md                  # Project overview
├── DIRECTORY_GUIDE.md         # This file
├── backend/                   # FastAPI backend (Python)
├── frontend/                  # Next.js frontend (TypeScript/React)
└── pip/                       # Publishable Python package (btc-mcp)
```

---

## `backend/` — FastAPI Server

The core API server. Handles agent deployment, MCP client sessions, payments, authentication, and Docker-based sandboxing.

| Technology | Purpose |
|---|---|
| **FastAPI** | REST + WebSocket API framework |
| **Uvicorn** | ASGI server |
| **MongoDB** (Motor/AsyncMongoClient) | Persistent storage (agents, users, creators, stakes) |
| **Redis** | Ephemeral state & caching (LNURL auth challenges) |
| **Docker** | Isolated containers for user-deployed MCP servers |
| **Lightspark** | Lightning Network payments (invoices, payouts) |
| **Anthropic (Claude)** | LLM powering the MCP client chat sessions |
| **MCP (FastMCP)** | Standardized agent/tool protocol |
| **sentence-transformers** | Vector embeddings for semantic agent search |
| **bolt11** | Lightning invoice encoding/decoding |
| **JWT / PyJWT** | Session tokens for creator authentication |
| **coincurve** | Signature verification (LNURL-auth) |
| **lnurl** | LNURL protocol encoding |
| **tiktoken** | Token counting for billing |

```
backend/
├── server.py                          # Entry point — runs uvicorn on src.app:app
├── .env                               # Environment variables (secrets, DB URIs)
├── builds/                            # Docker build contexts (one dir per deployed MCP server)
│   └── <uuid>/                        # Each deployed server gets a unique UUID folder
├── venv/                              # Python virtual environment
└── src/
    ├── __init__.py
    ├── app.py                         # FastAPI app factory, CORS, router registration, lifespan
    ├── database/
    │   ├── __init__.py
    │   ├── mongo.py                   # MongoDB connection (AsyncMongoClient), get_db()
    │   ├── redis.py                   # Redis async client instance
    │   └── embed.py                   # SentenceTransformer embeddings (all-MiniLM-L6-v2)
    ├── l402/
    │   ├── __init__.py
    │   └── l402.py                    # L402 payment offers, Lightning invoice creation, USD↔sats
    ├── middleware/
    │   ├── __init__.py
    │   └── middleware.py              # Auth middleware — creator_session (JWT) & user_session (Bearer)
    ├── routes/
    │   ├── agents.py                  # GET /api/agents — list/search agents (vector + text search)
    │   ├── creator.py                 # /creator/* — LNURL-auth sign-in, session polling, JWT cookies
    │   ├── mcp_client.py             # /ws/chat/<id> — WebSocket MCP client, Anthropic chat loop
    │   ├── mcp_server.py             # POST /api/deploy — upload & deploy MCP servers in Docker
    │   ├── payments.py                # /api/payments/* — top-up, stake, withdraw, verify payments
    │   └── user.py                    # /user/user-signin — anonymous user creation (UUID-based)
    ├── scripts/
    │   ├── __init__.py
    │   ├── requirements.txt           # Script-specific dependencies
    │   ├── server.py                  # Standalone script server
    │   ├── create_test_data.py        # Seed test agents into MongoDB
    │   ├── test_data.json             # Sample agent data
    │   ├── test_lnurl_callback.py     # LNURL callback testing
    │   ├── test_payment_request.py    # Payment flow testing
    │   └── test_websocket_chat.py     # WebSocket chat testing
    └── utils/
        ├── __init__.py
        └── logging.py                # Shared logger configuration
```

### Key API Routes

| Prefix | Router | Description |
|---|---|---|
| `/api` | `mcp_server` | Deploy MCP servers (Docker) |
| `/ws` | `mcp_client` | WebSocket chat with MCP agents |
| `/creator` | `creator` | LNURL-auth creator sign-in |
| `/user` | `user` | Anonymous user creation |
| `/api` | `agents` | Agent discovery & search |
| `/api/payments` | `payments` | Top-up, stake, withdraw |

---

## `frontend/` — Next.js Web App

The user-facing web application for browsing, deploying, chatting with, and staking on MCP agents.

| Technology | Purpose |
|---|---|
| **Next.js 16** | React framework (App Router) |
| **React 19** | UI library |
| **TypeScript** | Type-safe development |
| **Tailwind CSS 4** | Utility-first styling |
| **React Three Fiber / Drei** | 3D graphics (hero/decorative elements) |
| **Framer Motion** | Animations |
| **Axios** | HTTP client |
| **bolt11** | Lightning invoice decoding (client-side) |
| **qrcode** | QR code generation (Lightning invoices) |
| **Lucide React** | Icon library |

```
frontend/
├── package.json                       # Dependencies & scripts
├── next.config.ts                     # Next.js configuration
├── tsconfig.json                      # TypeScript configuration
├── eslint.config.mjs                  # ESLint config
├── postcss.config.mjs                 # PostCSS (Tailwind) config
├── next-env.d.ts                      # Next.js type declarations
├── app/
│   ├── layout.tsx                     # Root layout — font, Navbar, AuthProvider, session check
│   ├── page.tsx                       # Landing page — hero section with city image
│   ├── globals.css                    # Global styles (Tailwind)
│   ├── not-found.tsx                  # 404 page
│   ├── chat/
│   │   └── [slug]/
│   │       └── page.tsx               # Chat interface with a specific agent
│   ├── create/
│   │   └── page.tsx                   # Deploy a new MCP server (file upload form)
│   ├── explore/
│   │   ├── page.tsx                   # Browse & search agents
│   │   └── [slug]/
│   │       └── page.tsx               # Agent detail page
│   └── payments/
│       └── page.tsx                   # Top-up credits / payment management
├── components/
│   ├── AgentCard.tsx                  # Agent preview card (explore grid)
│   ├── AgentDetails.tsx               # Full agent details view
│   ├── AgentView.tsx                  # Agent page wrapper
│   ├── AuthContext.tsx                # React context for creator auth state
│   ├── HeroButton.tsx                 # Animated CTA button on landing page
│   ├── Loader.tsx                     # Loading spinner
│   └── Navbar.tsx                     # Top navigation bar
├── hooks/                             # Custom React hooks (empty)
├── lib/
│   └── utils.js                       # Shared utility functions
├── types/
│   └── global.d.ts                    # Global TypeScript type declarations
└── public/
    └── assets/
        └── images/                    # Static images (icons, backgrounds)
```

### Key Pages

| Route | File | Description |
|---|---|---|
| `/` | `app/page.tsx` | Landing page |
| `/explore` | `app/explore/page.tsx` | Browse all agents |
| `/explore/[id]` | `app/explore/[slug]/page.tsx` | Agent detail page |
| `/chat/[id]` | `app/chat/[slug]/page.tsx` | Chat with an agent |
| `/create` | `app/create/page.tsx` | Deploy a new MCP server |
| `/payments` | `app/payments/page.tsx` | Purchase credits |

---

## `pip/` — btc-mcp Python Package

A pip-installable Python package that lets any developer connect their AI agent to the btc-mcp network. Provides LangChain-compatible tools for agent discovery, chat, and automatic Lightning payments.

| Technology | Purpose |
|---|---|
| **LangChain Core** | Tool interface (`@tool` decorator) |
| **Lightspark SDK** | Automated Lightning payments |
| **httpx** | HTTP client for API calls |
| **websockets** | Persistent WebSocket connections for chat |
| **bolt11** | Invoice decoding |
| **Pydantic** | Input validation (content blocks) |

```
pip/
├── setup.py                           # Package metadata & install config (name: btc-mcp)
├── requirements.txt                   # Runtime dependencies
├── README.md                          # Package documentation
├── LICENSE.txt                        # MIT License
├── MANIFEST.in                        # Files to include in distribution
└── src/
    ├── example.py                     # Example usage with LangGraph ReAct agent
    ├── Penguins.txt                   # Sample data file for the example
    └── btc_mcp/
        ├── __init__.py
        ├── tools.py                   # LangChain tools: search_agents, start_chat,
        │                              #   continue_chat, end_chat, top_up, get_max_spend
        └── lightspark_client.py       # Lightspark wrapper — pay_invoice, spending limits
```

### Exported Tools (`BTC_MCP_TOOLS`)

| Tool | Description |
|---|---|
| `search_agents` | Discover agents by keyword (vector or exact search) |
| `start_chat` | Open a WebSocket session with an agent |
| `continue_chat` | Send follow-up messages in an active session |
| `end_chat` | Close the WebSocket session |
| `top_up` | Purchase credits via Lightning invoice |
| `get_max_spend` | Check remaining payment budget |

### Usage

```python
from btc_mcp.tools import BTC_MCP_TOOLS, init_lightspark_client

init_lightspark_client(client_id, secret, node_id, node_password)

# Use BTC_MCP_TOOLS with any LangChain-compatible agent
agent = create_react_agent(model=llm, tools=BTC_MCP_TOOLS)
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                       │
│         Browse · Deploy · Chat · Pay · Stake                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────────┐
│                     Backend (FastAPI + Uvicorn)                  │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌───────────────┐  │
│  │  Agents  │  │  MCP     │  │ Payments  │  │  Creator Auth │  │
│  │  Search  │  │  Client  │  │ (L402)    │  │  (LNURL/JWT)  │  │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘  └───────────────┘  │
│       │              │              │                            │
│  ┌────▼──────────────▼──────────────▼────────────────────────┐  │
│  │  MongoDB (agents, users, creators, stakes)                │  │
│  │  Redis (LNURL challenges, ephemeral state)                │  │
│  │  Sentence-Transformers (vector search embeddings)         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                           │                                     │
│              ┌────────────▼────────────┐                        │
│              │  Docker Containers      │                        │
│              │  (Deployed MCP Servers)  │                        │
│              │  FastMCP + Uvicorn       │                        │
│              └─────────────────────────┘                        │
└─────────────────────────┬───────────────────────────────────────┘
                          │ Lightning Network
              ┌───────────▼───────────┐
              │   Lightspark Node     │
              │   (Bitcoin/Lightning) │
              └───────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│               pip package (btc-mcp)                             │
│  Python client for programmatic agent interaction               │
│  LangChain tools + Lightspark auto-payments                     │
│  Connects to Backend via HTTP + WebSocket                       │
└─────────────────────────────────────────────────────────────────┘
```
