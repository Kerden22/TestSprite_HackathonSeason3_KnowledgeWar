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
        
        # -> Click the 'Features' link in the top navigation to scroll down the page.
        # Features link
        elem = page.locator('[id="navFeaturesLink"]')
        await elem.click(timeout=10000)
        
        # -> Click the 'Features' link in the top navigation to scroll down the page.
        # Home link
        elem = page.get_by_role('link', name='Home', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the 'Features' link in the top navigation to scroll to the features section, then click the 'Home' link to return to the hero.
        # Features link
        elem = page.locator('[id="navFeaturesLink"]')
        await elem.click(timeout=10000)
        
        # -> Click the 'Features' link in the top navigation to scroll to the features section, then click the 'Home' link to return to the hero.
        # Home link
        elem = page.get_by_role('link', name='Home', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the 'Features' link to scroll down the page, then click the 'Home' link to return to the hero.
        # Features link
        elem = page.locator('[id="navFeaturesLink"]')
        await elem.click(timeout=10000)
        
        # -> Click the 'Home' link in the top navigation to return to the hero section.
        # Home link
        elem = page.get_by_role('link', name='Home', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the 'Features' link, then click the 'Home' link and verify the hero contains 'AI-POWERED' or 'LEARNING PLATFORM'.
        # Features link
        elem = page.locator('[id="navFeaturesLink"]')
        await elem.click(timeout=10000)
        
        # -> Click the 'Features' link, then click the 'Home' link and verify the hero contains 'AI-POWERED' or 'LEARNING PLATFORM'.
        # Home link
        elem = page.get_by_role('link', name='Home', exact=True)
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> Verify the 'Features' link is visible in the top navigation
        await page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[3]").nth(0).scroll_into_view_if_needed()
        # Assert: Expected 'Features' link to be visible in the top navigation.
        await expect(page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[3]").nth(0)).to_be_visible(timeout=15000), "Expected 'Features' link to be visible in the top navigation."
        
        # --> Verify the 'Log in' button is visible in the header
        await page.locator("xpath=/html/body/nav/div/div/div[2]/div[3]/div[1]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Expected 'Log in' button to be visible in the header.
        await expect(page.locator("xpath=/html/body/nav/div/div/div[2]/div[3]/div[1]/button[1]").nth(0)).to_be_visible(timeout=15000), "Expected 'Log in' button to be visible in the header."
        
        # --> Verify the 'Home' link is visible in the navigation
        await page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Expected the 'Home' link to be visible in the navigation.
        await expect(page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[1]").nth(0)).to_be_visible(timeout=15000), "Expected the 'Home' link to be visible in the navigation."
        
        # --> Verify the 'Tournaments' nav link is NOT visible for guests
        # Assert: Expected the 'Tournaments' navigation link to not be visible to guests.
        await expect(page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[4]").nth(0)).not_to_be_visible(timeout=15000), "Expected the 'Tournaments' navigation link to not be visible to guests."
        
        # --> Verify the '⚔️ Tournaments' header button is NOT visible for guests
        # Assert: Expected the '⚔️ Tournaments' header button to not be visible to guests.
        await expect(page.locator("xpath=/html/body/nav/div/div/div[1]/div[2]/a[4]").nth(0)).not_to_be_visible(timeout=15000), "Expected the '\u2694\ufe0f Tournaments' header button to not be visible to guests."
        # Assert: Verify the home hero section with id 'home' is visible and shows 'AI-POWERED' or 'LEARNING PLATFORM'
        assert False, "Expected: Verify the home hero section with id 'home' is visible and shows 'AI-POWERED' or 'LEARNING PLATFORM' (could not be verified on the page)"
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    