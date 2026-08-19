🛍️ AI Shopping Assistant

An AI-powered smartphone shopping assistant that combines query understanding, hybrid search, RRF fusion, cross-encoder re-ranking, RAG, and an LLM to help users find smartphones based on natural-language requirements.

The application is built as an end-to-end retrieval-augmented generation system. Instead of sending a user's query directly to an LLM, the system first searches a local smartphone knowledge base, retrieves relevant products, re-ranks them, and then provides the retrieved product information to the LLM to generate a grounded recommendation.

Problem Statement

Choosing a smartphone can be difficult because users usually describe what they want in natural language rather than using exact product keywords.

For example, a user might ask:

"Suggest me a Samsung smartphone under ₹50,000 with good performance and a good camera."

A traditional keyword search may struggle with this type of query because:

Users may use different words to describe the same requirement.
Important constraints such as brand and budget need to be understood.
Semantic similarity is different from exact keyword matching.
Simply retrieving products is not enough; the results need to be presented as useful recommendations.

An LLM alone is also not sufficient because it may generate recommendations that are not grounded in the available product catalog.

That's where this project comes into play.

The AI Shopping Assistant combines traditional information retrieval with semantic search and an LLM:

User Query
    ↓
Query Understanding
    ↓
Query Rewriting
    ↓
BM25 + Vector Search
    ↓
RRF Fusion
    ↓
Cross-Encoder Re-ranking
    ↓
Retrieved Products
    ↓
RAG Context
    ↓
LLM
    ↓
Shopping Recommendation

The goal is to demonstrate an end-to-end RAG + LLM shopping assistant rather than a simple chatbot that sends every question directly to an LLM.

How the Application Works

A user interacts with the assistant through a Streamlit interface.

For example:

User:
Suggest me a Samsung smartphone under ₹50,000

The system processes the request through several stages.

1. Query Understanding

The application identifies relevant information from the user's request, such as:

Brand: Samsung
Maximum Price: ₹50,000

It also prepares a cleaner search query for retrieval.

2. BM25 Keyword Search

The query is searched using BM25 keyword retrieval.

BM25 is useful when the query contains exact terms such as:

Samsung
12GB RAM
256GB storage
Snapdragon
200MP camera
Specific smartphone models
3. Vector Search

The query is also converted into an embedding and searched semantically against the product knowledge base.

The project uses:

sentence-transformers/all-MiniLM-L6-v2

Vector search helps retrieve products that are semantically relevant even when the wording is different.

4. Hybrid Search

The BM25 and vector-search results are combined.

                 User Query
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
     BM25 Search          Vector Search
          │                     │
          └──────────┬──────────┘
                     ▼
                RRF Fusion

This allows the system to benefit from both exact keyword matching and semantic similarity.

5. RRF Fusion

The rankings from the different retrieval methods are combined using Reciprocal Rank Fusion (RRF).

The result is a unified ranking of candidate products.

6. Cross-Encoder Re-ranking

The retrieved candidates are passed through a cross-encoder to improve the final ordering.

Hybrid Search
     ↓
RRF
     ↓
Candidate Products
     ↓
Cross-Encoder
     ↓
Re-ranked Products

The highest-quality candidates are then used as context for the RAG pipeline.

7. RAG

The retrieved products are converted into context for the LLM.

User Query
     +
Retrieved Products
     ↓
Context Construction
     ↓
Prompt
     ↓
LLM

The LLM therefore has access to the products retrieved from the project's knowledge base instead of relying only on its pretrained knowledge.

8. LLM Recommendation

The LLM generates the final natural-language shopping recommendation using:

The user's query
Conversation context
Retrieved products
Relevant product constraints

The result is displayed in the Streamlit application.

Conversational Shopping

The assistant supports follow-up queries using conversation context.

For example:

User:
Suggest me a Samsung smartphone under ₹50,000.


Assistant:
Here are some suitable Samsung smartphones...


User:
What about the second one?


Assistant:
The second option is ...

The conversation state allows the assistant to understand references to previously retrieved products.

Retrieval Evaluation

The retrieval system is evaluated rather than assuming that one retrieval approach is automatically better.

The project evaluates multiple retrieval approaches:

BM25
Vector Search
Hybrid Search + RRF

The evaluation uses retrieval metrics such as:

Precision@K
Recall@K
Mean Reciprocal Rank (MRR)

The retrieval approaches are compared to identify the strongest retrieval strategy for the application.

Run retrieval evaluation with:

make evaluate

or:

uv run python evaluate.py
LLM Evaluation

The final LLM response is evaluated separately from retrieval.

The project compares different prompting approaches to determine which produces better shopping recommendations.

The evaluation considers factors such as:

Relevance
Groundedness
Constraint adherence
Answer quality

Run the LLM evaluation with:

make evaluate-llm

or:

uv run python evaluate_llm.py
User Feedback

The application allows users to provide feedback on generated recommendations.

Users can indicate whether the response was useful:

👍 Positive
👎 Negative

The feedback is associated with the corresponding request and stored in the monitoring database.

Example:

Request ID: 11
User Query: suggest me a samsung smartphone under 50000
Feedback: positive

This feedback can be analyzed through the monitoring dashboard.

Monitoring

Every assistant request can be monitored through the local SQLite monitoring database.

The system records information including:

Timestamp
User query
Search query
Query type
Filters
Retrieved product IDs
Number of retrieved products
Search latency
LLM latency
Total latency
Model
Input tokens
Output tokens
Total tokens
LLM cost
Generated response
Errors
User feedback

The monitoring database is:

monitoring.db
Monitoring Dashboard

A separate Streamlit dashboard provides visibility into application performance.

The dashboard includes:

Total requests
Error rate
Average latency
Search latency
LLM latency
Token usage
LLM cost
Requests by query type
Slowest requests
Most expensive requests
Recent requests
User feedback

Start the monitoring dashboard with:

make dashboard

or:

uv run streamlit run monitoring_dashboard.py

The dashboard runs separately from the main shopping assistant.

Dataset

The project currently uses a smartphone-only dataset containing 500 products.

The dataset is located at:

data/products_500.json

The products contain information such as:

Product ID
Brand
Product name
Price
Rating
Description
Specifications

The dataset is included with the project so that the retrieval pipeline can be reproduced locally.

Ingestion and Index Building

The product dataset is loaded and indexed using:

build_index.py

The indexing process:

products_500.json
       ↓
Product Processing
       ↓
Product Embeddings
       ↓
SQLite Product Database
       ↓
Search Index

Build or rebuild the product index using:

make index

or:

uv run python build_index.py

The current ingestion process is implemented as a Python script.

Project Structure
shopping_assistant/
│
├── app.py
├── assistant.py
│
├── hybrid_search.py
├── search.py
├── rag.py
├── prompt.py
│
├── build_index.py
├── database.py
├── embeddings.py
│
├── evaluate.py
├── evaluate_llm.py
│
├── monitoring.py
├── monitoring_analysis.py
├── monitoring_dashboard.py
│
├── data/
│   └── products_500.json
│
├── pyproject.toml
├── uv.lock
├── Makefile
└── README.md
Technologies
Component	Technology
Language	Python
Dependency Management	uv
UI	Streamlit
Database	SQLite
Keyword Search	BM25
Semantic Search	Sentence Transformers
Embedding Model	all-MiniLM-L6-v2
Hybrid Retrieval	BM25 + Vector Search
Rank Fusion	RRF
Re-ranking	Cross-Encoder
Generation	OpenAI LLM
Architecture	RAG
Monitoring	SQLite + Streamlit
Evaluation	Retrieval + LLM Evaluation
Setup

The project uses uv for Python dependency management.

Requirements

You need:

Python 3.12+
uv
OpenAI API key
1. Clone the Repository
git clone https://github.com/akshaypatil7015/shopping_assistant.git
cd shopping_assistant
2. Install Dependencies

Run:

uv sync

or:

make install

The uv.lock file is included to keep dependency versions reproducible.

3. Configure the API Key

Create a .env file in the project root:

OPENAI_API_KEY=your_api_key_here

Do not commit the .env file to Git.

Build the Product Index

Before running the application, build the product index:

make index

or:

uv run python build_index.py
Run the Application

Start the Streamlit shopping assistant:

make app

or:

uv run streamlit run app.py

The application will normally be available at:

http://localhost:8501
Run the Monitoring Dashboard

Open another terminal and run:

make dashboard

or:

uv run streamlit run monitoring_dashboard.py
Makefile Commands

The project includes a Makefile to simplify common development commands.

Command	Description
make install	Install/synchronize project dependencies
make index	Build the smartphone product index
make app	Start the shopping assistant
make dashboard	Start the monitoring dashboard
make evaluate	Run retrieval evaluation
make evaluate-llm	Run LLM evaluation
make clean	Remove Python cache files


End-to-End Flow

                    ┌──────────────┐
                    │     User     │
                    └──────┬───────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Streamlit UI   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Query           │
                  │ Understanding   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Query Rewriting │
                  └────────┬────────┘
                           │
                 ┌─────────┴─────────┐
                 ▼                   ▼
          ┌────────────┐      ┌────────────┐
          │    BM25    │      │   Vector   │
          │   Search   │      │   Search   │
          └─────┬──────┘      └─────┬──────┘
                │                   │
                └─────────┬─────────┘
                          ▼
                  ┌───────────────┐
                  │  RRF Fusion   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Re-ranking    │
                  │ Cross-Encoder │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Retrieved     │
                  │ Products      │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │      RAG      │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │      LLM      │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Recommendation│
                  └───────┬───────┘
                          │
                 ┌────────┴────────┐
                 ▼                 ▼
          ┌─────────────┐   ┌─────────────┐
          │    User     │   │ Monitoring  │
          │  Feedback   │   │             │
          └──────┬──────┘   └──────┬──────┘
                 │                 │
                 └────────┬────────┘
                          ▼
                  ┌───────────────┐
                  │    SQLite     │
                  │   Monitoring  │
                  │    Database   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │  Monitoring   │
                  │   Dashboard   │
                  └───────────────┘


Current Limitations

The project is currently focused on demonstrating an end-to-end AI shopping assistant.

Current limitations include:

The dataset contains smartphones only.
The dataset currently contains 500 products.
The product database is local SQLite.
The monitoring database is local SQLite.
The application currently runs locally using Streamlit.
Ingestion is implemented using a Python script.
Docker deployment is not currently included.
The system is not yet designed for production-scale traffic.
Future Additions

The following improvements are planned for future versions of the project:

🔄 Automated Data Ingestion

Move from a Python-script-based ingestion process to an automated data pipeline using tools such as:

Kestra
Airflow
Prefect

The future pipeline could periodically collect, validate, transform, and index new product data automatically.

🐳 Dockerization

Containerize the complete application using Docker and Docker Compose so that the application, database, and supporting services can be started consistently across environments.

📦 Larger Product Catalog

Expand beyond the current 500-product smartphone dataset to support a larger and continuously updated product catalog.

🛒 Multiple Product Categories

Extend the assistant beyond smartphones to categories such as:

Laptops
Tablets
Headphones
Smartwatches
Cameras
TVs
Other electronics
📈 Improved Recommendation System

Introduce more advanced recommendation techniques using:

User preferences
Historical interactions
Feedback signals
Product popularity
Personalized ranking
👍 Feedback-Driven Improvement

Use collected positive and negative feedback to improve:

Retrieval quality
Re-ranking
Prompt design
Recommendation quality
🧪 Automated Testing

Build a comprehensive automated test suite covering:

Query understanding
Query rewriting
BM25 retrieval
Vector retrieval
Hybrid search
RRF
Re-ranking
RAG
Monitoring
User feedback
🔁 Continuous Evaluation

Create an automated evaluation pipeline that periodically evaluates retrieval and LLM performance whenever the search pipeline or prompts are changed.

📊 Advanced Monitoring

Extend monitoring with additional metrics such as:

Retrieval quality over time
Feedback trends
Query success rate
RAG grounding quality
LLM response quality
Retrieval latency percentiles
Cost trends
Model comparison
🚀 Production Deployment

Move the application from local Streamlit execution toward a production architecture with:

API layer
Production database
Authentication
Scalable retrieval infrastructure
Container orchestration
CI/CD
Cloud deployment