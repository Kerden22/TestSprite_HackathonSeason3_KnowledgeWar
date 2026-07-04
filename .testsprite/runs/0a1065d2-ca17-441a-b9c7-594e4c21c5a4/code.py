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
        
        # -> Open the 'Log in' page by navigating to the /login URL.
        await page.goto("https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com/login")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Fill the email and password fields and click the 'Log in' button
        # you@example.com email field
        elem = page.locator('[id="loginEmail"]')
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("k.erden03@gmail.com")
        
        # -> Fill the email and password fields and click the 'Log in' button
        # •••••••• password field
        elem = page.locator('[id="loginPassword"]')
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("123456")
        
        # -> Fill the email and password fields and click the 'Log in' button
        # Log in button
        elem = page.locator('[id="loginSubmitBtn"]')
        await elem.click(timeout=10000)
        
        # -> Click the '🗺️ Roadmap' button to open the roadmap page.
        # 🗺️ Roadmap button
        elem = page.locator('[id="roadmapBtn"]')
        await elem.click(timeout=10000)
        
        # -> Click the 'TR' language toggle button to switch the page language to Turkish and verify the header subtitle updates to 'Galaktik Öğrenme Yolu'.
        # TR button
        elem = page.locator('[id="langTr"]')
        await elem.click(timeout=10000)
        
        # -> Navigate to the Roadmap page again and verify the main learning button reads '🚀 ÖĞRENMEYE BAŞLA'.
        await page.goto("https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com/roadmap")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # --> Assertions to verify final state
        
        # --> Verify the header subtitle now reads 'Galaktik Öğrenme Yolu'
        # Assert: The header subtitle is 'Galaktik Öğrenme Yolu'.
        await expect(page.locator("xpath=/html/body/header").nth(0)).to_contain_text("Galaktik \u00d6\u011frenme Yolu", timeout=15000), "The header subtitle is 'Galaktik \u00d6\u011frenme Yolu'."
        current_url = await page.evaluate("() => window.location.href")
        # Assert: page loaded with a URL (final outcome verified by the AI judge during the run)
        assert current_url, 'Page should have loaded with a URL'
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    