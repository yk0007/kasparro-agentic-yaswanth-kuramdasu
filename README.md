# Multi-Agent Content Generation System

A production-grade agentic automation system that generates structured, machine-readable content pages from product data.

## 🚀 Features

- **6 Specialized Agents**: Parser, Question Generator, FAQ, Product Page, Comparison, Output
- **LangGraph Orchestration**: StateGraph-based workflow with proper state management
- **LLM-Powered Logic Blocks**: Dynamic content generation for any product type
- **Dual LLM Provider Support**: 
  - **Groq** (Recommended): Fast generation with llama-3.3-70b
  - **Gemini**: Alternative with gemma-3-1b-it
- **Custom Template Engine**: Class-based templates with validation
- **Streamlit Demo UI**: Interactive interface for content generation
- **Machine-Readable Output**: 3 JSON files (FAQ, Product, Comparison)

## 📁 Project Structure

```
├── agents/             # 6 agent implementations
├── logic_blocks/       # LLM-powered content generation
├── templates/          # Template engine
├── orchestrator/       # LangGraph workflow
├── output/             # Generated JSON files
├── docs/               # Documentation
├── models.py           # Pydantic data models
├── config.py           # Configuration (API keys, models)
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

**Required API Keys:**
- `GROQ_API_KEY` - Groq API key (recommended, fast generation)
- `GEMINI_API_KEYS` - Google Gemini API key(s) (optional alternative)

### 5. Run the Application

```bash
streamlit run app.py
```

## 🔧 LLM Provider Options

| Provider | Content Model | Competitor Data | Recommendation |
|----------|---------------|-----------------|----------------|
| **Groq** | llama-3.3-70b | Fictional (fast) | ⭐ **Preferred** |
| **Gemini** | gemma-3-1b-it | Fictional | Alternative |

> **Note:** Groq is recommended for faster and more reliable content generation.

## 📖 Usage

1. **Select LLM Provider** in the sidebar (Groq recommended)
2. **Input Product Data**: Enter product JSON or use text fields
3. **Validate**: Click "Validate JSON" to check the input
4. **Generate**: Click "Generate Content" to run the multi-agent workflow
5. **View Results**: See generated content in FAQ, Product, and Comparison tabs
6. **Download**: Click download buttons to save JSON files

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

| File | Description |
|------|-------------|
| `faq.json` | 5+ categorized Q&A pairs |
| `product_page.json` | Complete product page content |
| `comparison_page.json` | Product A vs Competitor comparison |

## 📚 Documentation

See [docs/projectdocumentation.md](docs/projectdocumentation.md) for detailed system design and architecture.

## 🔑 Technologies

- **Python 3.10+**
- **LangChain** - Agent framework
- **LangGraph** - Workflow orchestration
- **Google Gemini API** - LLM with grounding
- **Groq API** - Fast LLM alternative
- **Pydantic** - Data validation
- **Streamlit** - Web UI
