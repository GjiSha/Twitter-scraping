import asyncio
from playwright.async_api import async_playwright
from CREDENTIALS import PASSWORD, USER_NAME
from Keywords import Keywords
keyword=Keywords[0]

async def initialize_browser():

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    return playwright, browser, page

async def login(page, username, password):
    await page.goto("https://twitter.com/login")
    
    # Username handling
    await page.wait_for_selector('input[autocomplete="username"]', state="visible")
    await page.fill('input[autocomplete="username"]', username)
    
    # Next button with proper XPath
    next_button_xpath = "//button//span[text()='Next']"
    await page.wait_for_selector(f"xpath={next_button_xpath}")
    await page.click(f"xpath={next_button_xpath}")  # Fixed selector usage
    
    # Password handling
    await page.wait_for_selector('input[type="password"]', state='attached')
    await page.fill('input[type="password"]', password)
    
    # Login button with corrected text match
    login_button_xpath = "//button//span[text()='Log in']/ancestor::button"  # Fixed text case
    await page.wait_for_selector(f"xpath={login_button_xpath}")
    await page.click(f"xpath={login_button_xpath}")
    
    # Login verification
    try:
        await page.wait_for_selector('a[aria-label="Home"]', timeout=15000)
    except Exception as e:
        raise RuntimeError(f"Login failed: {str(e)}")

async def twitter_search(page, keyword):
    # Target search input using ARIA attributes
    search_box = page.get_by_role("combobox",name="Search query")
    await search_box.click()
    
    # Type keyword and execute search
    await search_box.fill(keyword)
    await search_box.press("Enter")
    
    try:
        await page.wait_for_selector(f"text={keyword}", timeout=10000)  # Wait for up to 10 seconds
    except Exception as e:
        print(f"Timeout waiting for search results: {e}")
        return []





async def close_browser(playwright, browser):
    await browser.close()
    await playwright.stop()

async def main():
    playwright, browser, page = await initialize_browser()
    try:
        await login(page, USER_NAME, PASSWORD)
        results = await twitter_search(page, keyword)
        print("Search Results:")
        for result in results:
            print(result)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await close_browser(playwright, browser)

if __name__ == "__main__":
    asyncio.run(main())
