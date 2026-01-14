# Sovereign Learner System

**A Privacy-First, Agentic AI Framework for Sovereign Learning.**

The **Sovereign Learner System** is an advanced multi-agent architecture designed to allow users to leverage the power of state-of-the-art Cloud LLMs (like Google Gemini) while maintaining complete data sovereignty and privacy. It acts as a "Privacy Firewall" for your intellect.

## 🚀 Core Concept

In the age of AI, "you are what you query." This system ensures that your private research, learning gaps, and specific contexts (e.g., medical protocols, proprietary data) never leave your local machine in their raw form.

The system implements a **Semantic Generalization Pipeline**:
1.  **Local Intelligence (Phi-3.5)**: Runs entirely on your machine to analyze and "sanitize" your queries.
2.  **Cloud Handoff (Gemini 2.5)**: The sanitized, abstract query is sent to the cloud for heavy-lifting research.
3.  **Local Re-contextualization**: The cloud's answer is validated and translated back into your specific context locally.

## 🧠 Architecture

The system is orchestrated by **CrewAI** and consists of a team of specialized agents:

1.  **Privacy-Aware Manager**: Classifies queries into "Privacy Zones" (0-3).
    *   *Zone 0 (Offline)*: Handled entirely locally.
    *   *Zone 1 (Sovereign)*: Requires sanitization before cloud contact.
2.  **Semantic Generalizer**: Transforms sensitive entities (e.g., "CRISPR", "Patient-001") into abstract placeholders (e.g., "Protocol-X", "Subject-A").
3.  **Cloud Researcher**: Uses **Google Gemini 2.5 Flash** to answer the *generalized* query with deep technical knowledge, having zero awareness of the user's actual context.
4.  **Trust Enforcer**: Validates the cloud response for hallucinations, safety, and leaks.
5.  **Recontextualizer**: Maps the abstract cloud response back to the user's original context using the secure local mapping.
6.  **Competency Curator**: Stores the interaction in a local **ChromaDB** vector store to build a "Pedagogical Memory" that belongs only to you.

## 🛠️ Technology Stack

*   **Orchestration**: [CrewAI](https://crewai.com)
*   **Local LLM**: [Ollama](https://ollama.com) running `phi3.5` (Privacy Shield)
*   **Cloud LLM**: Google `gemini-2.5-flash` (Deep Knowledge)
*   **Memory**: [ChromaDB](https://www.trychroma.com/) (Local Vector Store)
*   **Language**: Python 3.10+

## 📋 Prerequisites

1.  **Python 3.10+** installed.
2.  **Ollama** installed and running.
    *   Pull the model: `ollama pull phi3.5`
3.  **Google API Key** for Gemini access.

## 🔧 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/madusankapremaratne/sovereign-learner.git
    cd sovereign-learner
    ```

2.  **Install Dependencies**
    Using `uv` (recommended) or `pip`:
    ```bash
    uv sync
    # OR
    pip install crewai crewai-tools langchain-google-genai google-generativeai chromadb python-dotenv
    ```

3.  **Configure Environment**
    Create a `.env` file in the root directory:
    ```bash
    cp .env.example .env  # If example exists, otherwise create new
    ```
    Add your keys:
    ```env
    GOOGLE_API_KEY=your_google_api_key_here
    MODEL=ollama/phi3.5
    API_BASE=http://localhost:11434
    ```

4.  **Dataset Setup (OULAD)**
    The project uses the Open University Learning Analytics Dataset (OULAD). Since data files are gitignored, you must set them up manually:
    
    1.  Create the directory structure:
        ```bash
        mkdir -p data/oulad
        ```
    2.  Download the OULAD dataset (CSV files) and place them inside `data/oulad/`.
    3.  Ensure the following files are present:
        *   `studentInfo.csv`
        *   `studentVle.csv`
        *   `vle.csv`
        *   `assessments.csv`
        *   `studentAssessment.csv`
        *   `courses.csv`
        *   `studentRegistration.csv`

## 🏃‍♂️ How to Run

Ensure Ollama is running (`ollama serve`), then execute the crew:

```bash
crewai run
```

Or via Python directly:
```bash
python src/sovereign_system/main.py
```

## 📂 Project Structure

```
sovereign_system/
├── knowledge/              # Local Persistent Memory
│   ├── chroma_db/          # Vector embeddings of your learning
│   └── user_preference.txt # User profile (Local only)
├── src/
│   └── sovereign_system/
│       ├── config/
│       │   ├── agents.yaml # Agent definitions & Model assignments
│       │   └── tasks.yaml  # Task workflows & Context binding
│       ├── tools/
│       │   ├── semantic_tools.py   # Generalization & Recontextualization logic
│       │   └── competency_tools.py # ChromaDB interactions
│       ├── crew.py         # Main Crew orchestration logic
│       └── main.py         # Entry point
└── README.md
```

## 🛡️ Privacy Zones

*   **Zone 0 (Offline)**: Personal thoughts, highly sensitive PII. *Never leaves local.*
*   **Zone 1 (Sovereign)**: Professional research, proprietary code. *Sanitized before Cloud.*
*   **Zone 2 (Opaque)**: General knowledge with slight context. *Minimal sanitization.*
*   **Zone 3 (Public)**: Weather, facts, public data. *Direct Cloud access.*

---
*Built with ❤️ for Data Sovereignty.*
