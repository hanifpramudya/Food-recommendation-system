# Food Recommendation System

A Python project for scraping food-related web images with Playwright, extracting
text from them with OCR, and parsing the text into structured menu tables with an
LLM.

## Setup

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies (already installed):
   ```bash
   uv pip install -r requirements.txt
   playwright install chromium
   ```

3. Install the Tesseract OCR engine:
   - macOS: `brew install tesseract tesseract-lang`
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - Windows: download installer from https://github.com/UB-Mannheim/tesseract/wiki

4. Configure your OpenAI API key:
   ```bash
   cp .env.example .env
   # Edit .env and set OPENAI_API_KEY
   ```

## Run the scraper

```bash
python scraping.py <url>
```

Example:

```bash
python scraping.py https://www.bbcgoodfood.com/recipes --output-dir images
```

## Parse a menu image to CSV

```bash
python ai_parsing.py path/to/menu.jpg --output menu.csv
```

The script:
1. Loads the image (local file or URL).
2. Runs OCR with pytesseract.
3. Sends the text to an LLM.
4. Saves a CSV with columns: `food_menu`, `description`, `price`.

## Files

- `requirements.txt` - Python dependencies
- `scraping.py` - Playwright image scraper
- `ai_parsing.py` - OCR + AI menu parser
- `.env.example` - Example environment variables
- `venv/` - Virtual environment
