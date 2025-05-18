# Multi-AI

A Python application that queries multiple LLM providers (OpenAI, Anthropic, Google Gemini) and uses a judge model to select the best response or blend multiple responses together.

## Features

- Query three different AI providers simultaneously:
  - OpenAI (GPT models)
  - Anthropic (Claude models)
  - Google (Gemini models)
- Uses a judge model to:
  - Select the best response
  - Or blend responses by weighting them
- Web interface for easy interaction
- Both CLI and API interfaces
- Deployable locally or to a web server

## Installation

1. Clone the repository:
   ```
   git clone [repo-url]
   cd multi-ai
   ```

2. Create a virtual environment:
   ```
   python -m venv multiai_env
   source multiai_env/bin/activate  # On Linux/Mac
   multiai_env\Scripts\activate     # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up API keys:
   ```
   python cli.py setup
   ```
   Then edit `.env` file with your API keys.

## Usage

### Web Interface

Start the web server:

```bash
python app.py
```

Then open your browser to http://localhost:8000 to access the web interface.

### CLI

Compare responses from multiple AI providers:

```bash
# Basic usage
python cli.py compare "Write a short story about a robot that learns to cook"

# Use specific models
python cli.py compare --openai gpt-4 --anthropic claude-3-opus-20240229 "Write a poem about AI"

# Blend responses instead of selecting one
python cli.py compare --blend "Explain quantum computing to a 10-year-old"

# Read prompt from file
python cli.py compare --file prompt.txt

# Save results to file
python cli.py compare --output results.json "Create a marketing plan for a new product"
```

List available models:

```bash
python cli.py models
```

### API Endpoints

The API will be available at http://localhost:8000 when you run the app.

- `GET /` - Web interface
- `GET /models` - List available models
- `POST /compare` - Compare responses from multiple models

Example API request:

```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain the theory of relativity",
    "models": {
      "openai": "gpt-4",
      "anthropic": "claude-3-sonnet-20240229",
      "gemini": "gemini-pro"
    },
    "blend": false,
    "include_details": true
  }'
```

## Configuration

Edit the `multi_ai/config.py` file to modify:
- Default models for each provider
- Available models list
- Timeout and retry settings

## Deployment

For web deployment, you can use services like:
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Run
- Azure App Service

The app is ready for deployment with minimal configuration changes.

## License

MIT