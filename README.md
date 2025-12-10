# Multi-Agent Content Generation System

A production-grade agentic automation system that generates structured, machine-readable content pages from product data.

## 🚀 Features

- **6 Specialized Agents**: Parser, Question Generator, FAQ, Product Page, Comparison, Output
- **LangGraph Orchestration**: StateGraph-based workflow with proper state management
- **5+ Reusable Logic Blocks**: Benefits, Usage, Ingredients, Safety, Comparison
- **Custom Template Engine**: Class-based templates with validation
- **Streamlit Demo UI**: Interactive interface for content generation
- **Machine-Readable Output**: 3 JSON files (FAQ, Product, Comparison)

## 📁 Project Structure

```
├── agents/             # 6 agent implementations
├── logic_blocks/       # 5+ reusable content logic
├── templates/          # Template engine
├── orchestrator/       # LangGraph workflow
├── output/             # Generated JSON files
├── docs/               # Documentation
├── models.py           # Pydantic data models
├── config.py           # Configuration
├── app.py              # Streamlit UI
└── requirements.txt    # Dependencies
```

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/kasparro-agentic-yaswanth-kuramdasu.git
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
# Edit .env and add your Gemini API key
```

### 5. Run the Application

```bash
streamlit run app.py
```

## 📖 Usage

1. **Input Product Data**: Enter product JSON in the input area (example provided)
2. **Validate**: Click "Validate JSON" to check the input
3. **Generate**: Click "Generate Content" to run the multi-agent workflow
4. **View Results**: See generated content in FAQ, Product, and Comparison tabs
5. **Download**: Click download buttons to save JSON files

## 🔧 Example Input

```json
{
  "name": "GlowBoost Vitamin C Serum",
  "concentration": "10% Vitamin C",
  "skin_type": ["Oily", "Combination"],
  "key_ingredients": ["Vitamin C", "Hyaluronic Acid"],
  "benefits": ["Brightening", "Fades dark spots"],
  "how_to_use": "Apply 2–3 drops in the morning before sunscreen",
  "side_effects": "Mild tingling for sensitive skin",
  "price": "₹699"
}
```

## 📤 Output Files

- `output/faq.json` - FAQ page with 5+ Q&As
- `output/product_page.json` - Comprehensive product page
- `output/comparison_page.json` - Product A vs fictional Product B

## 🏗️ Architecture

```
User Input → Parser Agent → Question Generator Agent
                                    ↓
              ┌──────────────┬──────────────┬─────────────────┐
              ↓              ↓              ↓
          FAQ Agent    Product Agent   Comparison Agent
              ↓              ↓              ↓
              └──────────────┴──────────────┘
                            ↓
                      Output Agent → JSON Files
```

## 📚 Documentation

See [docs/projectdocumentation.md](docs/projectdocumentation.md) for detailed system design.

## 📝 License

MIT License
