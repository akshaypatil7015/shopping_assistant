# 🛒 Shopping Assistant

An intelligent, agentic AI shopping assistant designed to transform the product discovery experience. Built with an Agentic Retrieval-Augmented Generation (Agentic RAG) architecture, this assistant helps users find products, compare options, ask detailed feature questions, and receive personalized recommendations grounded in e-commerce catalog data.

Unlike standard static search tools or basic chatbots, **Shopping Assistant** dynamically determines when to query its underlying database, executes precision vector searches, aggregates relevant product specs, and reasons over the context to deliver accurate, context-aware advice.

The project features a full end-to-end pipeline, complete with persistent vector indexing, offline evaluation benchmarks, an operational monitoring stack, an LLM-as-a-Judge quality framework, and an interactive frontend interface.

---

## 🎯 Problem Statement

Modern online shoppers encounter significant friction when trying to find products that specifically match their unique preferences, technical requirements, or budget constraints. Traditional e-commerce search tools and support solutions suffer from several core limitations:

- **Keyword Search Rigidness**: Standard search engines rely heavily on exact string matching or simple category filters. They struggle to parse complex, conversational queries like *"Find me an ergonomic wireless mouse under $50 with quiet clicks for programming"*.
- **Information Overload**: E-commerce platforms display hundreds of similar products, forcing users to manually open multiple tabs, read through lengthy product specifications, and decipher conflicting reviews.
- **Static Documentation & Unintelligent Bots**: Conventional customer support chatbots rely on decision trees or static FAQ matching, offering generic answers that fail to reason over specific product features or compare items effectively.
- **Lack of Personalization & Context**: Users often have follow-up questions about compatibility, material quality, or real-world usage that require synthesizing details across multiple spec sheets.

**Shopping Assistant** addresses these issues directly. By combining semantic vector retrieval with an agentic reasoning loop, it acts as a personal AI shopping companion—interpreting natural language intent, dynamically pulling exact product specifications from the knowledge base, comparing options, and delivering precise, factual, and grounded recommendations.

---

## ✨ Key Features

- **🤖 Agentic Retrieval-Augmented Generation (Agentic RAG)**: Dynamic tool invocation where the LLM decides when and how to search the product database based on user intent.
- **🔍 Persistent Semantic Retrieval**: Fast and relevant product matching powered by vector search.
- **🛠️ Extensible Tool Calling**: Clean separation between reasoning logic and data retrieval tools.
- **📊 Offline Evaluation Pipeline**: Comprehensive benchmarking for both retrieval precision and end-to-end agent response quality.
- **📈 Built-in Operational Monitoring**: Full observability into latency, token usage, execution steps, and total cost per interaction.
- **⚖️ Automated Quality Assessment**: Real-time answer evaluation using an **LLM-as-a-Judge** framework alongside explicit user feedback (👍 / 👎).
- **💬 Interactive UI**: Clean, easy-to-use Web UI (Streamlit) for seamless customer interaction.

---

## 🏗️ System Architecture

The architecture is structured as a set of decoupled, modular components designed for scalability and maintainability:

```text
┌────────────────┐     User Query      ┌──────────────────┐
│  Streamlit UI  │ ──────────────────► │  Shopping Agent  │
└────────────────┘                     └──────────────────┘
        ▲                                       │
        │ Grounded                              │ Tool Call / Search
        │ Response                              ▼
┌────────────────┐                      ┌──────────────────┐
│  LLM Engine    │ ◄─────────────────── │   Search Tool    │
└────────────────┘   Structured Context └──────────────────┘
        ▲                                       │
        │ Prompt Injection                      │ Query Execution
        │                                       ▼
┌────────────────┐                      ┌──────────────────┐
│ Prompt Builder │                      │  Vector Database │
└────────────────┘                      └──────────────────┘
```

1. **User Interface**: Captures natural language queries and renders interactive product suggestions.
2. **Agent Orchestrator**: Manages the conversational flow and determines when to trigger tools vs. respond directly.
3. **Search Tool**: Interacts with the persistent product catalog database to fetch top-k candidate items.
4. **Prompt Builder**: Formats retrieved product context, constraints, and instructions into a grounded prompt.
5. **LLM Engine**: Generates coherent, accurate, and non-hallucinated product summaries or recommendations.
6. **Monitoring Layer**: Logs metrics (latency, token consumption, cost) to PostgreSQL for real-time tracking.

---

## 🔄 End-to-End Workflow

1. **Query Submission**: The user enters a shopping query (e.g., *"What are the top noise-canceling headphones under $200?"*).
2. **Intent Analysis**: The Shopping Agent assesses whether catalog retrieval is necessary.
3. **Tool Execution**: If required, the agent calls the search tool with extracted search parameters (filters, category, query terms).
4. **Semantic Retrieval**: The retriever queries the vector database for matching products and specs.
5. **Context Ingestion**: Matching items, attributes, and stock details are injected into the reasoning prompt.
6. **Response Generation**: The LLM synthesizes the product details into a natural, comparative response.
7. **Telemetry & Feedback**: Metrics (response time, token counts, cost) are stored in PostgreSQL. The user can rate the response, and an LLM Judge assigns a quality score.

---

## 🛠️ Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Language** | Python 3.12+ |
| **LLM Engine** | Groq / OpenAI API |
| **Agent Framework** | Custom Tool-Calling Agent Architecture |
| **Retrieval & DB** | Persistent Vector Index / SQLite |
| **Frontend UI** | Streamlit |
| **Monitoring Storage** | PostgreSQL / Docker |
| **Evaluation Framework** | Pydantic, Structured Outputs |
| **Environment & Tooling** | `uv`, `python-dotenv` |

---

## 📚 Dataset & Ingestion

The assistant relies on a curated product catalog containing key attributes:
- **Product Metadata**: Name, Brand, Category, Price, Stock Status.
- **Detailed Specifications**: Features, dimensions, materials, usage scenarios.
- **Customer FAQs**: Product-specific questions and common user inquiries.

### Ingestion Pipeline
Raw product descriptions and metadata are embedded and indexed into a persistent vector database. Running `ingest.py` builds or updates the vector catalog.

---

## 🤖 Agent Workflow & Tool Calling

Unlike basic RAG setups that force a vector lookup on *every* input, the Shopping Assistant uses a tool-calling reasoning loop:

```text
User Input ──► Decision Node ──┬──► Direct Answer (e.g., "Hello! How can I help you today?")
                              │
                              └──► Tool Invocation ──► Search Catalog ──► Synthesize Results
```

- **Intent Recognition**: Distinguishes conversational chit-chat from specific product queries.
- **Query Parsing**: Extracts key filters like price caps, categories, and specific brand names.
- **Context Synthesis**: Summarizes complex multi-product comparisons cleanly.

---

## 📊 Evaluation & Quality Benchmarking

To ensure reliability, the repository includes a complete offline evaluation suite covering both **retrieval accuracy** and **agent response quality**.

### Ground Truth Generation
Evaluation questions were automatically generated across catalog items using structured output models:
- **Questions per Item**: 5 realistic shopper queries per catalog document.
- **Total Dataset**: Generated synthetic query set representing varied shopping intents.

### Retrieval Metrics
Evaluating how effectively the retriever isolates the correct product entries:

| Metric | Score | Description |
| :--- | :---: | :--- |
| **Hit Rate** | **97.1%** | Percentage of queries where the correct product appeared in Top-K results. |
| **MRR (Mean Reciprocal Rank)** | **0.889** | Evaluates how close to the top position the target item ranked. |

### End-to-End Agent Evaluation
Measures the full execution loop, verifying that the tool call trajectory was executed correctly and that final answers are strictly grounded without hallucinations.

---

## 📈 Monitoring & Observability

The application logs key operational parameters into PostgreSQL to provide full transparency:

- **Performance Metrics**: Latency (s), Total Tokens, Prompt Tokens, Completion Tokens.
- **Financial Metrics**: Estimated execution cost per query.
- **Quality Metrics**: LLM-as-a-Judge ratings (`✅ Relevant`, `🟡 Partly Relevant`, `❌ Non-Relevant`) and user feedback thumbs-up/down counts.

---

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.12 or higher
- **Package Manager**: [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `pip`
- **Containerization**: Docker (for running PostgreSQL monitoring database)
- **API Keys**: Groq / OpenAI API Key

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/akshaypatil7015/shopping_assistant.git
   cd shopping_assistant
   ```

2. **Install Dependencies**
   Using `uv`:
   ```bash
   uv sync
   ```
   Or using standard `pip`:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here

   # PostgreSQL Monitoring Configuration
   POSTGRES_HOST=localhost
   POSTGRES_DB=shopping_assistant
   POSTGRES_USER=user
   POSTGRES_PASSWORD=password
   ```

---

## ⚙️ Running the Application

### 1. Build the Product Vector Index
Ingest catalog data into the persistent vector database:
```bash
uv run python ingest.py
```

### 2. Start PostgreSQL Monitoring (Optional but Recommended)
Run the PostgreSQL container for logging metrics:
```bash
docker network create shopping-net

docker run -d \
    --name shopping-pg \
    --network shopping-net \
    -e POSTGRES_USER=user \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=shopping_assistant \
    -p 5432:5432 \
    -v pgdata:/var/lib/postgresql/data \
    postgres:17
```
Initialize database tables:
```bash
uv run python monitoring/db_init.py
```

### 3. Launch the User Interface
Run the main Streamlit interface:
```bash
uv run streamlit run app.py
```

### 4. Launch the Operational Dashboard
Open the monitoring dashboard on a separate port:
```bash
uv run streamlit run monitoring/dashboard.py --server.port 8502
```

---

## 🧪 Running Evaluations

Run the Jupyter notebooks in the `evaluation/` directory to reproduce benchmark scores:
- **Retrieval Evaluation**: `evaluation/01_ground_truth_and_search_eval.ipynb`
- **Agentic RAG Evaluation**: `evaluation/02_rag_evaluation.ipynb`

---

## 🚧 Future Roadmap

- [ ] **Multi-turn Conversation Memory**: Support complex follow-up questions across long shopping sessions.
- [ ] **External API Integration**: Real-time integration with live shop platforms (Shopify, WooCommerce API).
- [ ] **Multi-Modal Support**: Image-based product search and visual recommendation capabilities.
- [ ] **Asynchronous Evaluation**: Run LLM-as-a-Judge evaluations asynchronously via task queues (Celery/Redis).

---

## 🙏 Acknowledgments

Developed as an exploration into agentic AI workflows and LLM evaluation architectures. Special thanks to the open-source community and instructors at DataTalks.Club (LLM Zoomcamp) for operational frameworks and inspiration.
