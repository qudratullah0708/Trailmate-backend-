import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import json
import re
from datetime import datetime
from agents import function_tool
import time

# ANSI Color Codes
class Colors:
    HEADER = '\033[95m'      # Purple
    BLUE = '\033[94m'        # Blue
    GREEN = '\033[92m'       # Green
    YELLOW = '\033[93m'      # Yellow
    RED = '\033[91m'         # Red
    ENDC = '\033[0m'         # Reset color
    BOLD = '\033[1m'         # Bold
    UNDERLINE = '\033[4m'    # Underline

@function_tool
async def scrape_airbnb(
    location: str,
    guests: str,  # accept as string to prevent LLM schema type errors
    max_price: str,  # accept as string
    check_in: str,
    check_out: str,
    limit: str = "20"  # accept as string
):
    print(f"{Colors.YELLOW}[TOOL] scrape_airbnb called with location='{location}', guests={guests}, max_price={max_price}, check_in={check_in}, check_out={check_out}, limit={limit}{Colors.ENDC}")
    start_time = time.time()
    """
    Scrape Airbnb accommodation listings for a given location and date range.

    This tool navigates Airbnb's search page using Playwright, extracts listing
    details such as title, subtitle, price, area, rating, reviews, and URL, 
    and returns a list of available options up to the specified limit.

    Args:
        location (str): The destination city or area to search.
        guests (int): The number of guests.
        max_price (int): Maximum price per night in USD.
        check_in (str): Check-in date in YYYY-MM-DD format.
        check_out (str): Check-out date in YYYY-MM-DD format.
        limit (int, optional): Maximum number of listings to retrieve. Defaults to 20.

    Returns:
        list[dict]: A list of dictionaries, each containing details of a listing:
            - title (str): Listing title.
            - subtitle (str): Listing subtitle or description.
            - price (str): Price per night.
            - url (str): Direct URL to the listing.
            - location (str): Search location.
            - area (str): Specific area/neighborhood.
            - rating (str): Listing rating (if available).
            - reviews (str): Number of reviews (if available).
            - check_in (str): Check-in date.
            - check_out (str): Check-out date.
            - nights (int): Number of nights between check-in and check-out.

    Raises:
        Exception: If navigation, scraping, or page interaction fails at any step.

    Example:
        listings = await scrape_airbnb(
            location="Paris",
            guests=2,
            max_price=200,
            check_in="2025-09-15",
            check_out="2025-09-20",
            limit=10
        )
    """
    listings = []

    # Safely cast numeric parameters
    guests_int = int(guests)
    max_price_int = int(max_price)
    limit_int = int(limit)

    search_url = (
        f"https://www.airbnb.com/s/{location}/homes"
        f"?adults={guests_int}&price_max={max_price_int}"
        f"&check_in={check_in}&check_out={check_out}"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        print(f"{Colors.BLUE}[TOOL] Navigating to Airbnb search: {search_url}{Colors.ENDC}")
        await page.goto(search_url, timeout=60000)

        # Wait for listing cards to load
        await page.wait_for_selector("div[itemprop='itemListElement']", timeout=15000)

        while len(listings) < limit_int:
            try:
                await page.wait_for_selector("div[itemprop='itemListElement']", timeout=10000)
                cards = await page.query_selector_all("div[itemprop='itemListElement']")
                print(f"{Colors.BLUE}[TOOL] Found {len(cards)} listings on current page{Colors.ENDC}")

                for card in cards:
                    if len(listings) >= limit_int:
                        break

                    try:
                        title_el = await card.query_selector("div[data-testid='listing-card-title']")
                        title = (await title_el.inner_text()).strip() if title_el else "N/A"

                        subtitle = "N/A"
                        full_text = await card.inner_text()
                        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
                        if title in lines:
                            idx = lines.index(title)
                            if idx + 1 < len(lines):
                                subtitle = lines[idx + 1]

                        price = "N/A"
                        price_elements = await card.query_selector_all("span:has-text('$')")
                        if price_elements:
                            price = (await price_elements[-1].inner_text()).strip().replace('\n', ' ')

                        link_element = await card.query_selector("a")
                        relative_link = await link_element.get_attribute("href") if link_element else None
                        url = f"https://www.airbnb.com{relative_link}" if relative_link else "N/A"

                        area = "Unknown"
                        area_el = await card.query_selector("div:has-text(' in ')")
                        if area_el:
                            area_text = await area_el.inner_text()
                            if " in " in area_text:
                                area = area_text.split(" in ")[-1].split("\n")[0].strip()

                        rating = "N/A"
                        reviews = "N/A"
                        rating_el = await card.query_selector("span:has-text('('):has-text(')')")
                        if rating_el:
                            rating_text = await rating_el.inner_text()
                            match = re.match(r"(\d+\.\d+)\s*\((\d+)\)", rating_text)
                            if match:
                                rating, reviews = match.groups()
                            else:
                                rating_only = re.search(r"\d+\.\d+", rating_text)
                                review_count = re.search(r"\((\d+)\)", rating_text)
                                if rating_only:
                                    rating = rating_only.group()
                                if review_count:
                                    reviews = review_count.group(1)

                        listings.append({
                            "title": title,
                            "subtitle": subtitle,
                            "price": price,
                            "url": url,
                            "location": location,
                            "area": area,
                            "rating": rating,
                            "reviews": reviews,
                            "check_in": check_in,
                            "check_out": check_out,
                            "nights": (datetime.strptime(check_out, "%Y-%m-%d") - datetime.strptime(check_in, "%Y-%m-%d")).days
                        })

                    except Exception as e:
                        print(f"{Colors.RED}[TOOL] Error parsing listing: {e}{Colors.ENDC}")

                # Try to click next page if needed
                if len(listings) < limit_int:
                    next_btn = await page.query_selector("a[aria-label='Next']")
                    if next_btn:
                        try:
                            await next_btn.scroll_into_view_if_needed()
                            await next_btn.click(force=True)
                            print(f"{Colors.BLUE}[TOOL] Navigating to next page...{Colors.ENDC}")
                            await page.wait_for_selector("div[itemprop='itemListElement']", timeout=10000)
                        except PlaywrightTimeoutError as e:
                            print(f"{Colors.RED}[TOOL] Timeout while clicking next page. Exiting.{Colors.ENDC}")
                            break
                    else:
                        print(f"{Colors.YELLOW}[TOOL] No more pages.{Colors.ENDC}")
                        break

            except Exception as e:
                print(f"{Colors.RED}[TOOL] Error while scraping page: {e}{Colors.ENDC}")
                break

        await browser.close()
        duration = time.time() - start_time
        print(f"{Colors.GREEN}[TOOL] scrape_airbnb finished – {len(listings)} listings in {duration:.2f}s{Colors.ENDC}")
        return listings


# async def main():
#     location = "Paris"
#     guests = 5
#     max_price = 1500
#     check_in = "2025-09-15"
#     check_out = "2025-09-20"
#     limit = 36

#     print("Fetching listings...")
#     data = await scrape_airbnb(location, guests, max_price, check_in, check_out, limit)
#     print(json.dumps(data, indent=4, ensure_ascii=False))


# if __name__ == "__main__":
#     asyncio.run(main())
