# Emergency Communications Platform - Ghana

A real-time emergency communications platform for Ghana with AI-powered text summarization.

## Features

- **Real-time Weather Data**: Fetches weather information from Open-Meteo API
- **Agricultural Advisories**: Scrapes GHAAP agricultural data
- **CAP Alert Processing**: Handles Common Alerting Protocol (CAP) XML messages
- **AI Text Summarization**: Automatically summarizes advisory text using Ollama or OpenAI
- **Interactive 3D Map**: Displays Ghana regions with Three.js
- **Responsive UI**: Glass-morphism design with wider advisory cards

## Dual AI System

The platform now uses **two AI systems working together** for maximum intelligence:

### 🤖 **AI-Powered Web Scraping** (ScrapeGraphAI)
**Intelligently extracts data from GHAAP website**

**Priority Order**: ScrapeGraphAI with OpenAI → ScrapeGraphAI with Ollama → Traditional Scraping

1. **ScrapeGraphAI + OpenAI** (Primary)
   - Uses GPT models to understand webpage structure
   - Extracts structured agricultural data intelligently
   - Identifies weather, crop, and advisory information
   - Most accurate data extraction

2. **ScrapeGraphAI + Ollama** (Fallback)
   - Local AI for web scraping
   - Same intelligent extraction capabilities
   - No API costs but requires memory

3. **Traditional Scraping** (Final Fallback)
   - BeautifulSoup-based extraction
   - Always available as last resort

### 📝 **AI Text Summarization**
**Makes extracted content concise and readable**

**Priority Order**: OpenAI → Ollama → Intelligent Truncation

1. **OpenAI** (Primary, Recommended)
   - Most reliable and accurate summaries
   - Cloud-based GPT models
   - Requires API key (~$0.002 per request)
   - Works immediately with API key

2. **Ollama** (Fallback, Local)
   - Free and runs locally
   - Requires sufficient system memory (5.9GB+ for llama3)
   - No API costs
   - Automatic fallback if OpenAI unavailable

3. **Intelligent Truncation** (Final Fallback)
   - Always available
   - Preserves sentence/word boundaries
   - Better than simple character truncation

### Configuration

**Quick Start (Recommended)**:
1. Copy `.env.example` to `.env`
2. Add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
3. Restart the server - AI summarization will work immediately!

**Advanced Configuration**:
```bash
# OpenAI (Primary)
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Ollama (Fallback)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# Override default behavior (optional)
AI_SERVICE=openai
```

### How It Works

**Dual AI Processing Pipeline**:

1. **AI Web Scraping**: ScrapeGraphAI uses OpenAI/Ollama to intelligently extract structured data from GHAAP
2. **AI Text Summarization**: OpenAI/Ollama further summarizes the extracted text for UI display
3. **Smart Fallbacks**: Each step has intelligent fallbacks ensuring the system always works

**Data Flow**:
- GHAAP Website → **AI Scraping** → Structured Data → **AI Summarization** → Concise Advisory
- Original, intermediate, and final texts are all preserved
- Multiple AI models work together for maximum accuracy

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure AI service (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Open http://localhost:5000 in your browser

## Usage

- Click data source buttons to fetch real-time information
- Advisory cards now display AI-summarized text for better readability
- Cards are wider (500px) to accommodate longer text
- All original data is preserved for reference

## Dependencies

- Flask & Flask-SocketIO for web framework
- Requests & BeautifulSoup for web scraping
- OpenAI for AI summarization (optional)
- ScrapeGraphAI for enhanced scraping
- Three.js for 3D visualization
