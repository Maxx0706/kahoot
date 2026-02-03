import streamlit as st
import asyncio
import random
from playwright.async_api import async_playwright

# --- UI ---
st.set_page_config(page_title="Flash Bot", page_icon="⚡")
st.title("⚡ Flash Stealth Joiner")

pin = st.sidebar.text_input("Game PIN")
base_name = st.sidebar.text_input("Username", value="Player")
bot_count = st.sidebar.slider("Bots", 1, 15, 5)

# --- THE LIGHTNING ENGINE ---
async def join_sequence(browser, i, pin, name):
    """A high-speed stealth join"""
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
    # This script tricks Kahoot into thinking it's not a bot
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    page = await context.new_page()
    # Speed up: Block everything except the logic
    await page.route("**/*", lambda r: r.abort() if r.request.resource_type in ["image", "font", "media"] else r.continue_())
    
    try:
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="commit")
        await page.wait_for_selector("#nickname", timeout=5000)
        await page.fill("#nickname", f"{name}{i}{random.randint(10,99)}")
        await page.keyboard.press("Enter")
        await asyncio.sleep(60) # Keep them in the lobby
    except:
        pass

async def launch_attack():
    async with async_playwright() as p:
        # 'headless_shell' is the fastest version of Chromium
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu", "--single-process"])
        
        # Fire all tasks AT ONCE (Lightning speed)
        tasks = [join_sequence(browser, i, pin, base_name) for i in range(bot_count)]
        st.success(f"🔥 Launching {bot_count} bots simultaneously...")
        await asyncio.gather(*tasks)
        await browser.close()

if st.button("EXECUTE FLASH JOIN"):
    if pin:
        asyncio.run(launch_attack())
    else:
        st.error("PIN Required")
