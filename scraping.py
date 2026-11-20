#!/usr/bin/env python3
"""
Food Recommendation System - Web Image Scraper

Uses Playwright to scrape images from a webpage.
Includes a Google Images search mode that scrolls results and downloads
a fixed number of images.
"""

import argparse
import asyncio
import os
from urllib.parse import urlparse

from playwright.async_api import async_playwright


async def scrape_images(
    url: str,
    output_dir: str = "images",
    min_width: int = 100,
    min_height: int = 100,
    max_images: int = 0,
    scrolls: int = 0,
):
    """Scrape image URLs and download them from a webpage."""
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="networkidle")

        if scrolls > 0:
            for _ in range(scrolls):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(0.8)

        # Collect image elements with reasonable dimensions
        images = await page.query_selector_all("img")
        downloaded = 0

        for img in images:
            if 0 < max_images <= downloaded:
                break

            src = await img.evaluate("el => el.src") or await img.get_attribute("src")
            width = await img.evaluate("el => el.naturalWidth") or 0
            height = await img.evaluate("el => el.naturalHeight") or 0

            if not src or width < min_width or height < min_height:
                continue

            full_url = src if src.startswith("http") else ""
            if not full_url:
                # Try resolving relative URLs
                try:
                    full_url = await page.evaluate(f"new URL({src!r}, document.baseURI).href")
                except Exception:
                    continue

            ext = os.path.splitext(urlparse(full_url).path)[1] or ".jpg"
            filename = f"image_{downloaded:03d}{ext}"
            filepath = os.path.join(output_dir, filename)

            try:
                res = await context.request.get(full_url)
                if res.ok:
                    with open(filepath, "wb") as f:
                        f.write(await res.body())
                    print(f"Downloaded: {full_url} -> {filepath}")
                    downloaded += 1
            except Exception as e:
                print(f"Failed to download {full_url}: {e}")

        await browser.close()
        print(f"Total images downloaded: {downloaded}")


def main():
    parser = argparse.ArgumentParser(description="Scrape images from a webpage.")
    parser.add_argument("url", help="Target webpage URL")
    parser.add_argument(
        "--output-dir", "-o", default="images", help="Output directory for images"
    )
    parser.add_argument("--min-width", type=int, default=100, help="Minimum image width")
    parser.add_argument(
        "--min-height", type=int, default=100, help="Minimum image height"
    )
    parser.add_argument(
        "--max-images", "-n", type=int, default=0, help="Maximum images to download (0=unlimited)"
    )
    parser.add_argument(
        "--scrolls", "-s", type=int, default=0, help="Number of page scrolls before scraping"
    )
    args = parser.parse_args()

    asyncio.run(
        scrape_images(
            args.url,
            output_dir=args.output_dir,
            min_width=args.min_width,
            min_height=args.min_height,
            max_images=args.max_images,
            scrolls=args.scrolls,
        )
    )


if __name__ == "__main__":
    main()
