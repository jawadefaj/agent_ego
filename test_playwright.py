import asyncio
import sys
from playwright.async_api import async_playwright

# Instead of changing the policy, let's explicitly use ProactorEventLoop
if sys.platform == "win32":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)

async def main():
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://wikipedia.com")
        # print page info
        page
        print(await page.title())
        # sleep for 5 seconds
        await asyncio.sleep(5)
        await browser.close()

# Use the explicitly created loop
loop = asyncio.get_event_loop()
loop.run_until_complete(main())