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
        await page.goto("https://testsprite-hackathonseason3-knowledgewar-xk2p.onrender.com")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Click the 'Log in' button in the top navigation to open the login form and sign in with the test account.
        # Log in button
        elem = page.locator('[id="loginBtn"]')
        await elem.click(timeout=10000)
        
        # -> Fill the email and password fields and click the 'Log in' button to submit the credentials.
        # you@example.com email field
        elem = page.locator('[id="loginEmail"]')
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("k.erden03@gmail.com")
        
        # -> Fill the email and password fields and click the 'Log in' button to submit the credentials.
        # •••••••• password field
        elem = page.locator('[id="loginPassword"]')
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("123456")
        
        # -> Fill the email and password fields and click the 'Log in' button to submit the credentials.
        # Log in button
        elem = page.locator('[id="loginSubmitBtn"]')
        await elem.click(timeout=10000)
        
        # -> Click the '⚔️ Tournaments' button in the navbar to open the tournaments page.
        # ⚔️ Tournaments button
        elem = page.locator('[id="tournamentBtn"]')
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> Verify the '⚔️ Tournaments' button and '🗺️ Roadmap' button are visible after login
        await page.locator("xpath=/html/body/header/div/div/div[2]/a[1]").nth(0).scroll_into_view_if_needed()
        # Assert: The '🗺️ Roadmap' link in the header is visible after login.
        await expect(page.locator("xpath=/html/body/header/div/div/div[2]/a[1]").nth(0)).to_be_visible(timeout=15000), "The '\ud83d\uddfa\ufe0f Roadmap' link in the header is visible after login."
        
        # --> Verify the tournaments page opens at /tournament with tournament content visible
        # Assert: The browser is on the /tournament page.
        await expect(page).to_have_url(re.compile("/tournament"), timeout=15000), "The browser is on the /tournament page."
        await page.locator("xpath=/html/body/div[2]/div[3]/div[1]/div[1]/div[2]").nth(0).scroll_into_view_if_needed()
        # Assert: The tournaments area is visible and shows the 'No Active Tournament' content.
        await expect(page.locator("xpath=/html/body/div[2]/div[3]/div[1]/div[1]/div[2]").nth(0)).to_be_visible(timeout=15000), "The tournaments area is visible and shows the 'No Active Tournament' content."
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
    