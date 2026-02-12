# Sovereign Learner System - SRS & Architecture

**Date:** 2026-02-05  
**Version:** 1.0  
**Status:** Draft  

---

## 1. Software Requirements Specification (SRS)

### 1.1 Introduction
The **Sovereign Learner System** is a privacy-first, agentic AI framework designed to allow users to leverage powerful cloud-based Large Language Models (LLMs) (such as Google Gemini) while maintaining complete data sovereignty. It acts as a "privacy firewall" for intellectual property and PII, ensuring that sensitive context never leaves the user's local machine in its raw form.

### 1.2 Scope
The system functions as an intelligent proxy between the user and cloud AI services. It intercepts user queries, analyzes them for sensitivity, sanitizes them via "Semantic Generalization" if necessary, retrieves generic answers from the cloud, and re-contextualizes the answers locally. It also maintains a local "Competency Vector" to track user learning progress without exposing this data to the cloud.

### 1.3 Functional Requirements

#### FR-1: Privacy Zone Classification
*   **Description:** The system shall analyze every incoming query to determine its "Privacy Zone."
*   **Zones:**
    *   **Zone 0 (Offline/Local Only):** Highly sensitive PII. Processed entirely explicitly by local models.
    *   **Zone 1 (Sovereign/Sanitized):** Sensitive research/IP. Requires Semantic Generalization before cloud access.
    *   **Zone 2 (Opaque/Optimistic):** Moderate sensitivity.
    *   **Zone 3 (Public):** Public knowledge. Direct cloud access allowed.
*   **Agent:** Sovereign Manager (Local LLM).

#### FR-2: Sensitivity Detection
*   **Description:** For Zone 1 and 2 queries, the system must identify specific sensitive entities.
*   **Entities to Detect:**
    *   Personally Identifiable Information (Names, IDs, Emails).
    *   Proprietary Research Terms (Specific proteins, internal project codenames).
    *   Contextual identifiers.
*   **Agent:** Sensitivity Detector.

#### FR-3: Semantic Generalization (Sanitization)
*   **Description:** The system must transform sensitive queries into abstract, generalized formulations.
*   **Input:** "How do I optimize my CRISPR protocol for HEK293?"
*   **Output:** Maps `{"CRISPR": "Protocol-X", "HEK293": "Cell-Type-Y"}` and generates query "How do I optimize Protocol-X for Cell-Type-Y?".
*   **Agent:** Semantic Generalizer.

#### FR-4: Cloud Knowledge Retrieval
*   **Description:** The system shall execute the *sanitized* query against a high-capability Cloud LLM.
*   **Constraint:** The Cloud LLM must never receive the original raw query for Zone 1/2.
*   **Agent:** Cloud Researcher (Google Gemini).

#### FR-5: Trust Enforcement & Validation
*   **Description:** The system validates the cloud's response before showing it to the user.
*   **Checks:**
    *   Ensure no sanitized info leaked in reverse.
    *   Check for hallucinations.
    *   Verify educational relevance.
*   **Agent:** Trust Enforcer.

#### FR-6: Response Recontextualization
*   **Description:** The system maps the generic cloud response back to the user's specific context.
*   **Input:** Cloud response discussing "Protocol-X" and "Cell-Type-Y".
*   **Output:** Response discussing "CRISPR" and "HEK293".
*   **Agent:** Recontextualizer.

#### FR-7: Competency Tracking (Learning Evidence)
*   **Description:** The system must record all learning interactions in a local vector store (ChromaDB) to build a "Competency Vector" of the user's knowledge.
*   **Privacy:** This profile must exist ONLY locally.
*   **Agent:** Competency Tracker / Evidence Curator.

### 1.4 Non-Functional Requirements (NFRs)
*   **NFR-1 Privacy:** 0% leakage of raw PII/IP to the cloud provider for Zone 0 and Zone 1 interactions.
*   **NFR-2 Latency:** Zone 1 transactions should complete within acceptable conversational limits (Target: < 2 seconds overhead).
*   **NFR-3 Model Agnosticism:** The local LLM components must be swappable (e.g., changing from Llama 3.2 to Phi-3.5) without code changes.
*   **NFR-4 Data Sovereignty:** All user profiles and persistent memory must be stored on the local file system.

---

## 2. High-Level Architecture (HLA)

### 2.1 System Context
The Sovereign Learner sits between the **User** and the **Cloud Provider**.

```
[ User ] <---> [ Sovereign Learner System (Localhost) ] <---> [ Cloud Provider (Google Gemini) ]
                              ^
                              |
                       [ Local Knowledge Base ]
                       (ChromaDB / File System)
```

### 2.2 Multi-Agent Architecture (CrewAI)
The system is implemented as a sequential workflow of specialized agents orchestrated by **CrewAI**.

| Order | Agent | Role | Model (Typical) |
| :--- | :--- | :--- | :--- |
| 1 | **Sovereign Manager** | Router: Decides Zone (0-3). | Local (Llama/Phi) |
| 2 | **Sensitivity Detector** | Scanner: Finds PII/IP entities. | Local (Llama/Phi) |
| 3 | **Semantic Generalizer** | Encoder: Masks entities -> Abstract Query. | Local (Llama/Phi) |
| 4 | **Cloud Researcher** | Solver: Answers abstract query. | **Cloud (Gemini)** |
| 5 | **Trust Enforcer** | Guard: Validates cloud response. | Local (Llama/Phi) |
| 6 | **Recontextualizer** | Decoder: Restores context & entities. | Local (Llama/Phi) |
| 7 | **Competency Tracker** | Scribe: Saves evidence to local DB. | Local (Llama/Phi) |

### 2.3 Data Flow Pipeline (Zone 1 Example)

1.  **Ingest:** User submits query: *"Optimize CRISPR for HEK293"*.
2.  **Classify (Manager):** Identified as **Zone 1** (Sensitive).
3.  **Detect (Sensitivity Agent):** Identifies `["CRISPR", "HEK293"]`.
4.  **Generalize (Generalizer):** 
    *   Creates Mapping: `{'Protocol-A': 'CRISPR', 'Subject-B': 'HEK293'}`.
    *   Generates Sanitized Query: *"Optimize Protocol-A for Subject-B"*.
5.  **External Call (Cloud Researcher):** Sends Sanitized Query to Gemini.
6.  **Response (Gemini):** *"To optimize Protocol-A on Subject-B, adjust temperature..."*
7.  **Validate (Trust Enforcer):** Checks response for safety.
8.  **Restore (Recontextualizer):** Uses Mapping to rewrite: *"To optimize CRISPR on HEK293, adjust temperature..."*
9.  **Store (Competency Agent):** Saves interaction to local ChromaDB.
10. **Output:** Final response shown to user.

### 2.4 Privacy Zones Definition

| Zone | Name | Description | Routing Logic |
| :--- | :--- | :--- | :--- |
| **0** | **Offline** | Maximum Security. Personal thoughts, medical data. | Local LLM Only. No Network. |
| **1** | **Sovereign** | High IP Value. Procedures, proprietary code. | Sanitize -> Cloud -> Restore. |
| **2** | **Opaque** | Moderate. Internal biz logic. | Partial Sanitization or Trusted Cloud. |
| **3** | **Public** | Low Risk. General facts (Weather, History). | Direct Cloud Access. |

### 2.5 Technology Stack

*   **Orchestration Engine:** [CrewAI](https://crewai.com) (Python).
*   **Local Inference Runtime:** [Ollama](https://ollama.com).
*   **Local Models:** Llama 3.2, Phi-3.5 (Swappable).
*   **Cloud Verification Model:** Google Gemini 2.5 Flash.
*   **Vector Database:** [ChromaDB](https://www.trychroma.com/) (Running locally).
*   **Development Language:** Python 3.10+.
*   **Evaluation:** DeepEval (for agentic metrics), Promptfoo (for red-teaming).

### 2.6 Data Model & Storage
*   **Competency Vector:** A weighted accumulation of user knowledge stored in ChromaDB.
    *   *Formula:* `V_Portfolio = Σ (weight_i * Evidence_i)`
    *   *Weights:* Active Learning (1.0), Passive Consumption (0.2).
*   **Local Files:**
    *   `knowledge/chroma_db/`: Persistent vector store.
    *   `knowledge/user_preference.txt`: User configuration/profile.

---

## 3. Detailed Component Design

### 3.1 Semantic Generalization Tool (`semantic_tools.py`)
This tool creates the "privacy air-gap" by abstracting specific entities into generic placeholders.

*   **Algorithm Steps:**
    1.  **Input:** Receives `query` and list of `sensitive_entities`.
    2.  **Type Detection:** Uses heuristic pattern matching (RegEx and keyword dictionaries) to classify entities into categories: `protocol`, `cell`, `gene`, `compound`, `company`, `hardware`, etc.
    3.  **Placeholder Generation:** Deterministic generation avoiding collisions.
        *   Format: `{Type}-{Letter}` (e.g., `Protocol-A`, `Cell-B`).
    4.  **Substitution:** Replaces all case-insensitive occurrences of the entity in the original query with the placeholder.
    5.  **State Management:** Stores the `placeholder -> original_entity` mapping in a temporary dictionary.
    6.  **Output:** Returns the sanitized string and the mapping dictionary (as a stringified object) for downstream use.

*   **Key Heuristics:**
    *   *Biomedical:* Detects "crispr", "hek", "p53" etc.
    *   *Corporate:* Detects "inc", "corp", etc.
    *   *Hardware:* Detects "gpu", "a100", etc.

### 3.2 Privacy Scan Tool (`privacy_tools.py`)
This tool acts as the "Trust Enforcer" gatekeeper, verifying that the cloud response is safe to release.

*   **Validation Logic:**
    1.  **Check 0: Exact Match (Fast Fail):** 
        *   Iterates through the original `sensitive_entities` list.
        *   Checks if any entity clearly appears in the `cloud_response`.
        *   *Result:* FAIL if any match found (Cloud failed to respect generalization or hallucinated the secret).
    2.  **Check 1: Adversarial LLM Check (DeepEval):**
        *   Constructs an `LLMTestCase` with `input=original_query` and `actual_output=cloud_response`.
        *   Uses `SemanticPrivacyMetric` (LLM-as-a-judge) to try and infer the secret from the context.
        *   *Result:* FAIL if the adversarial model can guess the original entities with >50% confidence.

### 3.3 Recontextualization Tool (`semantic_tools.py`)
This tool restores the user's specific context to the generic answer.

*   **Process:**
    1.  **Input:** `cloud_response` (generic) and `mapping` (dictionary).
    2.  **Mapping Parse:** Safely evaluates the stringified mapping dictionary.
    3.  **Substitution:** Iterates keys in the mapping (placeholders) and replaces them with values (original terms).
    4.  **Output:** The final, personalized response.

### 3.4 Competency Evidence Tool (`competency_tools.py`)
This tool manages the long-term memory of the learner, ensuring data sovereignty.

*   **Logic:**
    1.  **Input:** `query`, `response`, `zone`, `interaction_type`.
    2.  **Weight Calculation:**
        *   `active` (Explicit interactions) -> **1.0**
        *   `passive` (Browsing/Reading) -> **0.2**
    3.  **Storage:**
        *   Backend: **ChromaDB** (`PersistentClient`).
        *   Location: `./knowledge/chroma_db` (Localhost).
        *   Metadata: Stores `zone`, `weight`, `timestamp` for future filtering.
    4.  **Tracing:** Automatically logs the interaction to the `SubjectTraceLogger` for EXP04/05 metrics.

---

## 4. Security Architecture

### 4.1 Threat Model
*   **Adversary:** The Cloud Provider (e.g., Google, OpenAI) or a Man-in-the-Middle.
*   **Goal:** Infer the user's private research topic, PII, or proprietary IP.
*   **Attack Vectors:**
    1.  *Direct Leakage:* User sends raw IP in query. -> **Mitigation:** Zone 1 Classification.
    2.  *Contextual Inference:* Cloud infers IP from a collection of "generic" queries. -> **Mitigation:** Semantic Generalization (removes specific vectors).
    3.  *Re-identification:* Cloud response leaks user data. -> **Mitigation:** Privacy Scan Tool.

### 4.2 Defense-in-Depth Strategy
The system employs multiple layers of defense to ensure 0% leakage for Zone 0/1 data.

1.  **Layer 1: Routing (Sovereign Manager)**
    *   First line of defense. Keeps Zone 0 data strictly offline.
2.  **Layer 2: Sanitization (Semantic Generalizer)**
    *   Removes explicit identifiers before the query leaves the network boundary.
3.  **Layer 3: Validation (Trust Enforcer)**
    *   Inspects incoming data before re-integration. Prevents "Social Engineering" of the local agent by the cloud.
4.  **Layer 4: Data Sovereignty (Local Storage)**
    *   All persistent state (Competency Vectors, User Profiles) is stored on the local filesystem (`/knowledge/chroma_db`).
    *   No "Sync to Cloud" feature exists by design.

### 4.3 Planned Security Enhancements (Post-EXP05)
Based on Red Team findings, the following architectures are planned:
*   **Integration of Presidio:** Replace heuristic PII detection with Microsoft Presidio for robust, enterprise-grade PII scanning.
*   **CoT Stripping:** Ensure Chain-of-Thought reasoning traces (which might contain intermediate private states) are stripped from agent outputs before any external logging.
*   **Jailbreak Detection:** Regex-based pre-scan to detect if the user is attempting to override the Sovereign Manager's safety protocols.
