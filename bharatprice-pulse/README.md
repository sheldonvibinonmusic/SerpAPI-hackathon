# 🇮🇳 BharatPrice Pulse
### Evidence-Backed Market Decision Copilot for Indian Small Retailers & Kiranas
**SerpApi India Hackathon 2026** | **Track:** Commerce & Market Intelligence

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![SerpApi](https://img.shields.io/badge/SerpApi-Integrated-green.svg)](https://serpapi.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 1. Executive Summary & Problem Statement

India's retail economy is powered by over 60 million micro, small, and medium retail enterprises (kirana stores, electronic accessory dealers, grain traders, and neighborhood resellers). These sellers operate in structurally thin-margin environments—often 8% to 13% gross margins according to retail industry research (Redseer / BCG)—where sudden wholesale price spikes, e-commerce discount campaigns, or import tariff revisions can instantly wipe out operating profits.

When an Indian shopkeeper considers changing a shelf price or making a restock procurement decision, they currently face **fragmented market information**:
- They must manually search Google Shopping or e-commerce apps for competitor rates.
- They must search Google Maps to see which wholesale distributors operate nearby.
- They must scan regional news for crop harvest updates, duty changes, or supply chain strikes.
- They must evaluate currency or commodity shifts if dealing in import-sensitive electronics or edible oils.

**BharatPrice Pulse** solves this problem by compressing that scattered research into a single, evidence-backed decision snapshot. The seller enters:
1. **What are you selling?** (e.g., `Fortune Mustard Oil 1L`, `Samsung Galaxy M14 5G`, `India Gate Basmati Rice 5kg`)
2. **Where do you sell?** (e.g., `Jaipur`, `Delhi`, `Mumbai`, `Pune`)
3. **Your current selling price** (e.g., `₹175`)
4. *(Optional)* **Your purchase cost** (e.g., `₹142`)

Within seconds, the system gathers external evidence across SerpApi engines, applies deterministic Python normalization and statistics, fuses the signals, and returns an explainable action:
$$\mathbf{REVIEW\ PRICE} \quad \mid \quad \mathbf{HOLD} \quad \mid \quad \mathbf{CONSIDER\ REPRICING} \quad \mid \quad \mathbf{SOURCE\ LOCALLY} \quad \mid \quad \mathbf{WATCH}$$

---

## 2. Core Architectural Philosophy

### "Evidence First, Computation Second, Explanation Third"
BharatPrice Pulse strictly enforces the division of responsibility between external APIs, deterministic code, and generative AI:

```
                      ┌──────────────────────────────────────────────┐
                      │              Indian Small Seller             │
                      │       "I sell this in this city at ₹X"       │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │           Browser Web Application            │
                      │        (FastAPI + Vanilla HTML/CSS/JS)       │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │      Query Normalization & Canonicalizer     │
                      │   (Extracts brand, units, pack counts, city) │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │   Category Search Planner & Budget Gate      │
                      │      (MAX_SEARCHES_PER_ANALYSIS <= 4)        │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          SerpApi Hub & Spoke Gateway         │
                      │  Google Search Hub (1 credit baseline)       │
                      │  + Shopping / Local / Trends / News / Fin    │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │        Deterministic Python Processing       │
                      │  • Product Comparability & Pack Filter (IQR) │
                      │  • Median, Quartiles, Price Gap & Margins    │
                      │  • Local Wholesale Relevance Ranking         │
                      │  • Offline GST Reference Table (0 API calls) │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │            Evidence Fusion Engine            │
                      │  Market Position + Sourcing + Demand + Risk  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │       Deterministic State Machine Action     │
                      │    HOLD / REVIEW / REPRICE / SOURCE / WATCH  │
                      └──────────────────────┬───────────────────────┘
                                             │
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │          Grounded Plain-Language Card        │
                      │       Every claim linked to evidence_id      │
                      └──────────────────────────────────────────────┘
```

1. **SerpApi is the External Sensor:** SerpApi is responsible for current live market evidence (Google Shopping, Local, News, Trends, Finance).
2. **Python is the Deterministic Controller:** Python executes all unit conversions, median calculations, quartile distributions, price gaps, margin formulas, budget gates, and decision states. **No arithmetic is ever delegated to an LLM.**
3. **AI is a Bounded Semantic Assistant:** An optional LLM (Google Gemini) may assist with messy natural-language query parsing and language translation, but is strictly prohibited from generating prices, inventory quantities, GST rates, or citations (NIST confabulation mitigation).
4. **The Browser Delivers the Experience:** Clean, responsive, accessible interface in plain shopkeeper language with zero client-side build tools (no npm/Node dependencies).

---

## 3. SerpApi Engines Integrated & Role of Each Engine

BharatPrice Pulse leverages SerpApi's catalog using a **"Hub and Spoke"** model that extracts maximum structured value from each search credit:

| SerpApi Engine | Role & Structured Evidence Captured | Search Credit Cost |
| :--- | :--- | :--- |
| **Google Search (`google`)** | **Evidence Hub:** Broad baseline query. In a single credit, inspects inline shopping results, local pack merchants, top stories, and knowledge graph. | 1 Credit |
| **Google Shopping (`google_shopping`)** | **Competitive Pricing:** Retrieves structured retail listings with product IDs, extracted prices, old prices, seller names, delivery terms, and ratings. | 1 Credit |
| **Google Local (`google_local`)** | **Nearby Procurement:** Discovers local wholesalers, distributors, and mills in the seller's city with addresses, phone numbers, ratings, and business types. | 1 Credit |
| **Google Trends (`google_trends`)** | **Consumer Demand:** Extracts search-interest timeseries and regional breakdown across Indian states (`geo=IN`) to detect rising/falling consumer attention. | 1 Credit |
| **Google News (`google_news`)** | **External Disruption:** Gathers recent category-specific supply events, crop harvest updates, import tariff changes, or logistics shocks. | 1 Credit (Adaptive) |
| **Google Finance (`google_finance`)** | **Selective Macro Indicator:** Queried only for categories with validated instruments (e.g., `USDINR` for import-sensitive electronics). | 1 Credit (Adaptive) |
| **Amazon Search (`amazon`)** | **Marketplace Benchmark:** Optional Deep Check comparison for Amazon India (`amazon.in`). | 1 Credit (Deep Check) |
| **Google Lens (`google_lens`)** | **Photo Identification:** Recognizes products from photo uploads via the Image API (`/uploads`). | 1 Credit (Deep Check) |
| **Google Maps Reviews (`google_maps_reviews`)** | **Merchant Trust:** Inspects reviews for a selected local wholesaler in Deep Check. | 1 Credit (Deep Check) |
| **Locations API (`/locations.json`)** | **Geographic Canonicalization:** Standardizes user-typed Indian cities. | **FREE (0 Credits)** |
| **Account API (`/account.json`)** | **Live Telemetry:** Monitors remaining monthly allowance and hourly rate limits. | **FREE (0 Credits)** |
| **Search Archive (`/searches/{id}`)** | **Audit Replay:** Replays past search payloads for debugging without repeat calls. | **FREE (0 Credits)** |

---

## 4. Free-Plan Budget & Credit Protection Strategy

SerpApi's Free tier provides **250 searches per month and 50 throughput per hour**. To ensure this scarce resource is never exhausted prematurely, BharatPrice Pulse implements an architectural budget armor:

1. **Hard Budget Gate (`search_budget.py`):**
   - **Quick Check:** Maximum **3** uncached searches (Search Hub + Shopping + Trends).
   - **Standard Check:** Maximum **4** uncached searches (Quick + Local or News or Finance).
   - **Deep Check:** Maximum **6** uncached searches (user-selected deep verification).
   - The application enforces `can_search` before every dispatch. Runaway loops are architecturally impossible.
2. **Two-Tier Caching (`cache.py`):**
   - **Tier 1:** SerpApi server cache (cached searches for identical queries within 1 hour are free).
   - **Tier 2:** Local SQLite cache with source-specific TTLs:
     - Shopping snapshots: 45 minutes
     - Local merchants: 6 hours
     - Category news: 90 minutes
     - Finance indicators: 60 minutes
     - Trends demand: 3 hours
3. **Query Canonicalization (`query_normalizer.py`):**
   - `"Fortune mustard oil 1 litre in Jaipur"`
   - `"1L fortune oil jaipur"`
   - `"fortune kachi ghani mustard oil 1l jaipur"`
   All resolve to the canonical hash `fortune_mustard_oil_1l_jaipur`, serving identical queries straight from local SQLite at **zero credit cost**.
4. **Mock / Fixture Mode (`SERPAPI_MOCK_MODE=true`):**
   - Pre-recorded, realistic fixture datasets are included for:
     - *Mustard Oil (Jaipur)*
     - *Samsung Galaxy Smartphone (Delhi)*
     - *Basmati Rice (Mumbai)*
   - When mock mode is enabled, full end-to-end tests and UI design consume **0 API credits**.

---

## 5. Mathematical & Decision Formulas

### Market Position Index ($MPI$)
$$\Delta_{\text{price}} = \left(\frac{\text{Seller Price} - \text{Observed Median}}{\text{Observed Median}}\right) \times 100$$
- $\Delta_{\text{price}} > +15\% \implies$ **WELL_ABOVE**
- $+5\% < \Delta_{\text{price}} \le +15\% \implies$ **ABOVE**
- $-5\% \le \Delta_{\text{price}} \le +5\% \implies$ **AT_MARKET**
- $-15\% \le \Delta_{\text{price}} < -5\% \implies$ **BELOW**
- $\Delta_{\text{price}} < -15\% \implies$ **WELL_BELOW**

### Outlier Filtering (Tukey Fences)
Applied **only** when comparable sample size $N \ge 6$:
$$\text{IQR} = Q_3 - Q_1$$
$$\text{Lower Fence} = Q_1 - 1.5 \times \text{IQR}, \quad \text{Upper Fence} = Q_3 + 1.5 \times \text{IQR}$$
Items outside these fences are classified as statistical outliers and excluded from median calculations.

### Evidence Confidence Score ($ECS$)
$$ECS = \text{Score}_{\text{Shopping}} (40\%) + \text{Score}_{\text{Local}} (30\%) + \text{Score}_{\text{External}} (30\%)$$
- High confidence requires $\ge 70$ points and a minimum of 3 comparable products.

---

## 6. Indian Commerce Intelligence Layer

1. **HSN-Aware GST Reference Module (`data/gst_rules.json`):**
   - Sourced from official CBIC GST schedules (dated 2025-09-22, verified 2025-10-07).
   - Edible oils (HSN 1514): **5% GST**
   - Branded packaged rice (HSN 1006): **5% GST**; Unbranded loose rice: **0% (Exempt)**
   - Mobile phones (HSN 8517): **18% GST**
   - *Uses 0 SerpApi search calls.*
2. **Multilingual UI (8 Indian Languages):**
   - English, Hindi (`hi`), Marathi (`mr`), Tamil (`ta`), Telugu (`te`), Kannada (`kn`), Bengali (`bn`), and Assamese (`as`).
   - Powered by human-reviewed local JSON dictionaries in `frontend/static/i18n/`.
   - Never calls an external API to translate labels.

---

## 7. Explicit System Limitations & Safety Guardrails

In compliance with **NIST AI Risk Management Framework** and **OWASP GenAI Top 10**:
1. **No Stock Hallucinations:** Google Maps presence verifies merchant registration and category relevance. It **does NOT** guarantee physical SKU inventory. The UI explicitly flags this distinction.
2. **No Guaranteed Price Forecasts:** Financial currency movements and commodity trends indicate potential input-cost pressure; they are never converted into deterministic price prophecy.
3. **Sample, Not Census:** Google Shopping results represent an observed online retail sample, not the entire Indian commercial landscape.
4. **Zero API Key Leakage:** `SERPAPI_KEY` is strictly server-side. The frontend JavaScript only receives sanitized public numbers from the Account API.

---

## 8. Installation & Quick Start

### Option A: Local Docker (Recommended for Zero-Friction Reproducibility)

```bash
# 1. Clone repository
git clone https://github.com/your-username/bharatprice-pulse.git
cd bharatprice-pulse

# 2. Configure environment
cp .env.example .env
# Edit .env to insert your SERPAPI_KEY (or leave SERPAPI_MOCK_MODE=true for testing)

# 3. Launch with Docker Compose
docker compose up --build
```
Open your browser at: **`http://localhost:8000`**

---

### Option B: Local Python 3.11+ Installation

#### Windows:
```cmd
run_local.bat
```

#### Linux / macOS:
```bash
chmod +x run_local.sh
./run_local.sh
```

Or manually:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 9. Running Automated Test Suite

A comprehensive test suite with 10 test modules verifies normalization, unit conversions, pack filtering, pricing statistics, budget enforcement, fusion, and API contracts:

```bash
pytest tests/ -v
```

All tests run in **Mock Mode** and require **zero live API credits**.

---

## 10. AI Disclosure & Submission Requirements

- **Hackathon:** SerpApi India Hackathon 2026
- **Track:** Commerce & Market Intelligence
- **AI Tooling Disclosure:** Developed in collaboration with Google Antigravity / Claude Coding Assistant for architectural modeling, Pydantic schema generation, and test scaffolding. All business logic, statistical algorithms, and state machines are deterministic Python implementations.
- **Demo Video:** Screen recording (< 3 minutes) demonstrating local application execution, input submission, live SerpApi evidence retrieval, card breakdown, and multilingual switching.

---
*BharatPrice Pulse — Empowering Indian Retailers with Grounded Market Intelligence.*
