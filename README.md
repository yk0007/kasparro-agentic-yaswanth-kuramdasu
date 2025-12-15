# Multi-Agent Content Generation System

A production-grade agentic automation system that generates structured, machine-readable content pages from product data.

## 🚀 Features

- **6 Specialized Agents**: Parser, Question Generator, FAQ, Product Page, Comparison, Output
- **LangGraph Orchestration**: StateGraph with parallel fan-out/fan-in execution
- **7 Logic Blocks**: Including cross-block analyzer with impact scoring & risk assessment
- **Quality Gates**: validate_content_node with conditional routing (pass OR fail-fast)
- **Hard Validation**: Template validation strictly enforced - no fallback outputs
- **Groq LLM Provider**: Fast generation with llama-3.3-70b-versatile
- **API Key Rotation**: Multi-key support with automatic retry on rate limits
- **Custom Template Engine**: Class-based templates with validation
- **Streamlit Demo UI**: Interactive interface for content generation
- **Machine-Readable Output**: 3 JSON files (FAQ, Product, Comparison)
- **15+ FAQ Questions**: With deduplication, scoring, and LLM regeneration loop
- **Test Suite**: 68 unit and integration tests included

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                     │
├─────────────────────────────────────────────────────────────┤
│  parse → generate_questions ─┬→ faq ──────────┐            │
│                              ├→ product_page ─┼→ validate  │
│                              └→ comparison ───┘    ↓       │
│                                              ┌─────┴─────┐  │
│                                              │  output   │  │
│                                              │    OR     │  │
│                                              │   END     │  │
│                                              └───────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Workflow Features:**

- **Fan-out**: 3 agents run in parallel after question generation
- **Fan-in**: All converge to `validate_content_node`
- **Conditional Routing**: Routes to `output` (success) OR `END` (fail-fast)

## 📁 Project Structure

```
├── agents/             # 6 agent implementations
├── logic_blocks/       # 7 blocks (benefits, safety, cross_block_analyzer, etc.)
├── templates/          # Template engine with hard validation
├── orchestrator/       # LangGraph workflow with quality gates
├── tests/              # 68 unit and integration tests
├── output/             # Generated JSON files
├── docs/               # Documentation
├── models.py           # Pydantic data models
├── config.py           # Groq config with API key rotation
├── utils.py            # Utility functions
├── app.py              # Streamlit UI
└── requirements.txt    # Dependencies
```

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yk0007/kasparro-agentic-yaswanth-kuramdasu.git
cd kasparro-agentic-yaswanth-kuramdasu
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Required API Key:**

- `GROQ_API_KEY` - Groq API key for LLM generation

### 5. Run the Application

```bash
streamlit run app.py
```

## 🔧 LLM Configuration

| Provider | Model                   | Use Case               |
| -------- | ----------------------- | ---------------------- |
| **Groq** | llama-3.3-70b-versatile | All content generation |

> **Note:** This system uses Groq exclusively. Competitor products are fictional (no external search).

## 📖 Usage

1. **Input Product Data**: Enter product JSON or use text fields
2. **Validate**: Click "Validate JSON" to check the input
3. **Generate**: Click "Generate Content" to run the multi-agent workflow
4. **View Results**: See generated content in FAQ, Product, and Comparison tabs
5. **Download**: Click download buttons to save JSON files

## ✅ Running Tests

```bash
python3 -m pytest tests/ -v
```

All 68 tests verify:

- **Assignment Requirements**: Product parsing, question generation, templates, logic blocks
- **Workflow Integration**: LangGraph uses parallel fan-out/fan-in
- **Workflow Resilience**: Error handling, fail-fast behavior, recovery state
- **No External Search**: Only internal data used
- **FAQ Generation**: 15+ questions with deduplication and scoring

## 🔧 Example Input

```json
{
  "name": "Your Product Name",
  "concentration": "Key differentiator",
  "skin_type": ["Target User 1", "Target User 2"],
  "key_ingredients": ["Feature 1", "Feature 2"],
  "benefits": ["Benefit 1", "Benefit 2"],
  "how_to_use": "Usage instructions",
  "side_effects": "Considerations or limitations",
  "price": "₹1999"
}
```

## 📊 Output Files

| File                   | Description                        |
| ---------------------- | ---------------------------------- |
| `faq.json`             | 5+ categorized Q&A pairs           |
| `product_page.json`    | Complete product page content      |
| `comparison_page.json` | Product A vs Competitor comparison |

## 📚 Documentation

See [docs/projectdocumentation.md](docs/projectdocumentation.md) for detailed system design and architecture.

## 🔑 Technologies

- **Python 3.10+**
- **LangChain** - Agent framework
- **LangGraph** - Workflow orchestration with `StateGraph`
- **Groq API** - Fast LLM (llama-3.3-70b-versatile)
- **Pydantic** - Data validation
- **Streamlit** - Web UI
