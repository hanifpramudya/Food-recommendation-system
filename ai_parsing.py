#!/usr/bin/env python3
"""
Food Recommendation System - AI Menu Parsing

Pipeline:
  1. Load a food-menu image (local file or URL).
  2. Run OCR with pytesseract to extract raw text.
  3. Use an LLM to parse the raw text into a structured table:
     food_menu (dish name), description, price.
  4. Save the result as a CSV file.

Environment variables (see .env.example):
  - OPENAI_API_KEY  : required for AI parsing
  - OPENAI_BASE_URL : optional (for OpenAI-compatible providers)
"""

import argparse
import json
import os
import re
import sys
from io import BytesIO

import pandas as pd
import pytesseract
import requests
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image


def load_image(image_source: str) -> Image.Image:
    """Load an image from a local path or URL."""
    if image_source.startswith("http://") or image_source.startswith("https://"):
        response = requests.get(image_source, timeout=30)
        response.raise_for_status()
        return Image.open(BytesIO(response.content))
    return Image.open(image_source)


def run_ocr(image: Image.Image) -> str:
    """Extract text from a PIL image using pytesseract."""
    return pytesseract.image_to_string(image)


def parse_menu_with_ai(raw_text: str, client: OpenAI, model: str = "gpt-4o-mini") -> pd.DataFrame:
    """Send raw OCR text to an LLM and return a structured DataFrame."""
    system_prompt = (
        "You are a helpful assistant that extracts structured food menu data from OCR text. "
        "Return ONLY a JSON array. Each object must have exactly these keys: "
        "'food_menu' (dish name), 'description' (brief description or empty string), "
        "and 'price' (as a string). If a value is missing, use an empty string."
    )

    user_prompt = (
        "Extract food menu items from the following OCR text and return a JSON array:\n\n"
        f"{raw_text}\n\n"
        "Example output:\n"
        '[\n  {"food_menu": "Margherita Pizza", "description": "Tomato, mozzarella, basil", "price": "$12.00"}\n]'
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.0,
    )

    content = response.choices[0].message.content or ""
    return _extract_menu_df(content)


def _extract_menu_df(content: str) -> pd.DataFrame:
    """Parse JSON array from LLM response into a DataFrame."""
    match = re.search(r"\[.*\]", content, re.DOTALL)
    if not match:
        raise ValueError(f"Could not find JSON array in LLM response:\n{content}")

    data = json.loads(match.group(0))
    df = pd.DataFrame(data)

    expected = {"food_menu", "description", "price"}
    if not expected.issubset(df.columns):
        raise ValueError(f"Missing expected columns. Got: {list(df.columns)}")

    return df[["food_menu", "description", "price"]]


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Parse a food-menu image into a CSV table.")
    parser.add_argument("image", help="Path or URL to the menu image")
    parser.add_argument("--output", "-o", default="menu_parsed.csv", help="Output CSV path")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.", file=sys.stderr)
        print("Copy .env.example to .env and add your key.", file=sys.stderr)
        sys.exit(1)

    base_url = os.getenv("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

    print(f"Loading image: {args.image}")
    image = load_image(args.image)

    print("Running OCR...")
    raw_text = run_ocr(image)
    if not raw_text.strip():
        print("No text detected in image.", file=sys.stderr)
        sys.exit(1)

    print("Parsing menu with AI...")
    df = parse_menu_with_ai(raw_text, client, model=args.model)

    df.to_csv(args.output, index=False)
    print(f"Saved {len(df)} menu items to {args.output}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
