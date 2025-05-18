# Multi-AI Comparison Tool

A web application that compares responses from multiple AI models and provides the best one. This tool supports:

- **OpenAI** (GPT-4, GPT-4o, o3)
- **Anthropic** (Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku)
- **Google Gemini** (Gemini Pro)

## Features

- Send a single prompt to multiple AI models
- Get responses from all models
- Select the best response using a judge model
- Blend responses from multiple models for collaborative answers
- Modern UI with responsive design and dark/light mode
- Interactive model selection and response viewing
- Markdown rendering with syntax highlighting

## Getting Started

### Prerequisites

- Python 3.9 or higher
- API keys for the AI providers you want to use

### Installation

1. Clone the repository:
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
```bash
cp .env.example .env
```

4. Edit the `.env` file to add your API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GEMINI_API_KEY=your_gemini_key
```

### Running the Application

Run the application with:

```bash
python app.py
```

Then open your browser and navigate to `http://localhost:8000`.

## Usage

1. Enter your prompt in the text area
2. Select the models you want to compare from each provider
3. Toggle "Blend responses" if you want a combined answer
4. Toggle "Show details" to see information about all responses
5. Click "Compare AI Responses" to get results
6. View the best response and all individual responses

## Development

### Setting Up Development Environment

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

### Running Tests

Run the tests with:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=multi_ai tests/
```

## Project Structure

```
multi_ai/
├── __init__.py
├── api.py             # FastAPI application
├── cli.py             # Command-line interface
├── config.py          # Configuration settings
├── models/            # AI model interfaces
│   ├── __init__.py
│   ├── anthropic_model.py
│   ├── base_model.py
│   ├── gemini_model.py
│   └── openai_model.py
├── services/          # Business logic
│   ├── __init__.py
│   ├── comparator.py
│   └── judge.py
├── static/            # Static assets
│   ├── css/
│   └── js/
├── templates/         # HTML templates
└── utils/             # Utility functions
    ├── __init__.py
    └── helpers.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.