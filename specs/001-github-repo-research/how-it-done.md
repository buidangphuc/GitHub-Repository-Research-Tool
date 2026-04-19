# 🚀 System Design & Post-Docs: AI-Native GitHub Repository Research Tool

### 💡 Architect’s Note: The Engineering Value
* **Core Philosophy:** This is not a thin LLM wrapper, but a resilient, async orchestration engine built for the AI era.
* **The Problem:** LLMs are inherently slow, expensive, and unpredictable, destroying standard API Latency SLOs.
* **The Solution:** Completely decoupled AI workloads from the core system using an event-driven, horizontally scalable architecture.

---

### 🏗️ Design Decisions (Short & Direct)
* **Strict AI Decoupling:** Stateless FastAPI (blazing fast) hands off heavy AI tasks to an isolated SQS/ElasticMQ async worker pool.
* **Hexagonal Architecture (Ports & Adapters):** All external services are behind abstract interfaces. 100% infrastructure replaceability and isolated testing.
* **Strict Pydantic Contracts:** Zero raw dictionaries. Every layer boundary is strictly typed to prevent silent data corruption.
* **Two-Tier Storage:** Redis for transient, sub-millisecond status polling; PostgreSQL for permanent, durable records.

---

### 🤖 AI Tool Usage ("Human-in-the-Loop")
* **Template Scaffolding:** Fed my battle-tested FastAPI template into Speckit, forcing the AI to generate Day-1 production-ready code (bypassing "sloppy AI" habits).
* **Rapid Prototyping:** Leveraged Figma AI for quick UI validation and AI diagramming tools for architecture visualization.
* **Human Blueprint:** The AI wrote the syntax; I dictated the architecture, system boundaries, and resilience strategies.

---

### 🚀 Future Improvements (Enterprise Scaling)
* **Full-Repo RAG (pgvector):** Move beyond READMEs by chunking and embedding the entire codebase to bypass token limits.
* **Interactive Chatbot:** Transform the static report into a conversational developer companion for specific codebase queries.
* **TTFT Optimization (Streaming):** Replace single-shot JSON with SSE/WebSockets to stream tokens directly to the UI, masking LLM latency.
* **Enterprise Auth & Token Quotas:** Implement an API Gateway with JWT and granular, Redis-backed sliding-window token budget limiters.