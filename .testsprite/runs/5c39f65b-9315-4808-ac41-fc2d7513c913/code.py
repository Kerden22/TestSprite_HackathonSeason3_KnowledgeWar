import asyncio
import re
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",
                "--disable-dev-shm-usage",
                "--ipc=host",
                "--single-process"
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        # Wider default timeout to match the agent's DOM-stability budget;
        # auto-waiting Playwright APIs (expect, locator.wait_for) inherit this.
        context.set_default_timeout(15000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> navigate
        await page.goto("https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com/")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Navigate to the home page anchor '#how-it-works' so the 'How it works' section is in view.
        await page.goto("https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com/#how-it-works")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Click the 'TR' button in the EN | TR language toggle in the header
        # TR button
        elem = page.locator('[id="langTr"]')
        await elem.click(timeout=10000)
        
        # -> Verify the header navigation shows the Turkish label 'Anasayfa'.
        # TR button
        elem = page.locator('[id="langTr"]')
        await elem.click(timeout=10000)
        
        # -> Click the 'TR' button in the EN | TR language toggle, then verify the header shows the Turkish label 'Anasayfa'.
        # TR button
        elem = page.locator('[id="langTr"]')
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> Verify the header navigation shows the Turkish label 'Anasayfa'
        # Assert: Expected the header navigation link to display the Turkish label 'Anasayfa'.
        await expect(page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[1]").nth(0)).to_have_text("Anasayfa", timeout=15000), "Expected the header navigation link to display the Turkish label 'Anasayfa'."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    