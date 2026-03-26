# Builder's OS

**Builder's OS** is a minimalist, AI-powered companion designed for developers who build in sessions. It helps you maintain momentum by providing context for where you left off, capturing what you've learned, and allowing you to query your own history using natural language.

The UI is intentionally designed with a warm, parchment-like aesthetic to create a focused, low-friction environment for building.

## Key Features

-   **Session Briefings**: Get a punchy, AI-generated summary of your last 7 days of work before you start.
-   **Structured Logging**: Quickly record what you built and what you learned in each session.
-   **Ask Your Logs**: Query your past session logs with natural language questions (e.g., "What did I learn about FastAPI routing?").
-   **Integrated Backlog**: Capture ideas and tasks instantly without leaving your workflow.
-   **Minimalist UI**: A clean, two-column layout with a warm, "paper-like" design.
-   **Local Storage**: All data is stored in simple Markdown files on your machine. No complex database required.

## Tech Stack

-   **Backend**: FastAPI (Python)
-   **AI Providers**: Google Gemini (default) or Anthropic Claude
-   **Frontend**: Single-file HTML/CSS/JavaScript (Vanilla)
-   **Storage**: Local Filesystem (Markdown)

## Prerequisites

-   Python 3.10 or higher
-   An API key for Google Gemini or Anthropic Claude

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/amitauti/builder-os.git
    cd builder-os
    ```

2.  **Set up a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Locate `config.yml` in the root directory (or create it based on the example below).
2.  Add your API key and set your preferred provider.

```yaml
llm_provider: "gemini"          # "gemini" or "claude"

gemini_api_key: "YOUR_GEMINI_KEY_HERE"
gemini_model: "gemini-2.0-flash"

claude_api_key: "YOUR_CLAUDE_KEY_HERE"
claude_model: "claude-3-5-sonnet-20240620"

vault_path: "/path/to/your/builder-os" # The absolute path to this directory
```

## Usage

1.  **Start the server**:
    ```bash
    ./start.sh
    ```
2.  **Open the UI**:
    Navigate to `http://localhost:8100` in your browser.
3.  **Stop the server**:
    ```bash
    ./stop.sh
    ```

## Project Structure

-   `main.py`: FastAPI backend handling API requests and LLM integration.
-   `index.html`: The single-page frontend.
-   `projects/`: Directory where session logs and status files are stored as Markdown.
-   `backlog.md`: A global list of ideas and tasks.
-   `config.yml`: Global configuration settings.

## License

MIT
