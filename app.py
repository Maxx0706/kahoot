import streamlit as st
import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- UI ---
st.set_page_config(page_title="Flash Joiner", page_icon="⚡")
st.title("⚡ Flash Stealth Joiner")

with st.sidebar:
    pin = st.text_input("Game PIN")
    name = st.text_input("Name", value="Player")
    count = st.slider("Bots", 1, 10, 5)
    delay = st.slider("Stagger Delay", 0.1, 2.0, 0.5)

# --- THE ENGINE ---
async def join_bot(browser, i, pin, base_name):
    # Use unique context to avoid session overlap
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        viewport={'width': 1280, 'height': 720}
    )
    
    page = await context.new_page()
    # Apply stealth to this specific page
    await stealth_async(page)
    
    try:
        # Load Kahoot
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="networkidle")
        
        # Look for the input - wait for it to actually be ready
        nickname_input = await page.wait_for_selector("#nickname", timeout=10000)
        
        # Human-like interaction
        await nickname_input.click()
        await page.keyboard.type(f"{base_name}{i}", delay=random.randint(50, 150))
        await page.keyboard.press("Enter")
        
        # Keep them in the lobby for 10 minutes
        await asyncio.sleep(600)
    except Exception:
        pass
    finally:
        await context.close()

async def run_flash():
    async with async_playwright() as p:
        # Launch with flags that hide 'automation'
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        tasks = []
        for i in range(1, count + 1):
            tasks.append(asyncio.create_task(join_bot(browser, i, pin, name)))
            # This tiny stagger prevents the "Target Closed" crash
            await asyncio.sleep(delay)
            
        st.success(f"🔥 {count} bots dispatched. Checking lobby...")
        await asyncio.gather(*tasks)
        await browser.close()

if st.button("EXECUTE JOIN"):
    if pin:
        asyncio.run(run_flash())
    else:
        st.error("PIN needed!")
