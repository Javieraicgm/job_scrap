import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Going to BNE...")
        await page.goto("https://www.bne.cl/ofertas?q=data", wait_until="networkidle")
        
        print("Waiting for job cards...")
        # Try to wait for the job list to render
        try:
            await page.wait_for_selector(".oferta", timeout=15000)
        except Exception as e:
            print("No .oferta found:", type(e))
        
        html = await page.content()
        with open("scratch/bne_playwright.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        # Try finding elements that might be job titles
        titles = await page.evaluate("Array.from(document.querySelectorAll('h2, h3, .titulo, .title')).map(el => el.innerText)")
        print("Found possible titles:", [t for t in titles if t.strip()][:10])
        
        await browser.close()

asyncio.run(main())
