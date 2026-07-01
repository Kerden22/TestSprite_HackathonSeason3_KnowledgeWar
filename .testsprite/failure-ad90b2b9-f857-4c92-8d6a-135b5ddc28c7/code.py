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
        
        # -> Click the '⚔️ Yarış ve Kazan' tournaments entry on the landing page to open the tournaments experience.
        # 4
        elem = page.get_by_text('4', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the '⚔️ Yarış ve Kazan' tournaments entry on the landing page and verify the tournaments experience is displayed.
        # 4
        elem = page.get_by_text('4', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the '⚔️ Yarış ve Kazan' tournaments entry on the landing page and verify the tournaments experience opens.
        # 4
        elem = page.get_by_text('4', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the '⚔️ Yarış ve Kazan' tournaments card on the landing page and verify the tournaments experience appears.
        # 4
        elem = page.get_by_text('4', exact=True)
        await elem.click(timeout=10000)
        
        # -> Click the 'Giriş Yap' (Login) button to open the login form so any authentication prerequisite for tournaments can be checked.
        # Giriş Yap button
        elem = page.locator('[id="loginBtn"]')
        await elem.click(timeout=10000)
        
        # -> Fill 'k.erden03@gmail.com' into the E-posta Adresi field, fill '123456' into the Şifre field, then click the 'Giriş Yap' button to sign in.
        # ornek@email.com email field
        elem = page.locator('[id="loginEmail"]')
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("k.erden03@gmail.com")
        
        # -> Fill 'k.erden03@gmail.com' into the E-posta Adresi field, fill '123456' into the Şifre field, then click the 'Giriş Yap' button to sign in.
        # •••••••• password field
        elem = page.locator('[id="loginPassword"]')
        await elem.wait_for(state="visible", timeout=10000)
        await elem.fill("123456")
        
        # -> Fill 'k.erden03@gmail.com' into the E-posta Adresi field, fill '123456' into the Şifre field, then click the 'Giriş Yap' button to sign in.
        # Giriş Yap button
        elem = page.locator('[id="loginSubmitBtn"]')
        await elem.click(timeout=10000)
        
        # --> Assertions to verify final state
        
        # --> Verify the tournaments experience is displayed
        # Assert: Tournaments experience is open (URL contains '/tournament').
        await expect(page).to_have_url(re.compile("/tournament"), timeout=15000), "Tournaments experience is open (URL contains '/tournament')."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    