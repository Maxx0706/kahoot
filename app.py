import streamlit as st
import asyncio
import os
import subprocess
from playwright.async_api import async_playwright

# --- 1. FORCE BROWSER INSTALLATION ---
def setup_playwright():
    # We force the install into a specific local folder we can control
    if not os.path.exists("./pw-browser"):
        with st.spinner("First-time setup: Downloading Chromium (this takes a minute)..."):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "./pw-browser"
            subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)

setup_playwright()

# --- 2. UI SETUP ---
st.title("🚀 Kahoot Load Tester")

with st.sidebar:
    pin = st.text_input("Kahoot Game PIN")
    name = st.text_input("Base Username", value="Bot")
    count = st.slider("Bot Count", 1, 25, 10)
    delay = st.slider("Join Delay (sec)", 0.1, 1.0, 0.3)

status = st.empty()
progress = st.progress(0)

# --- 3. BOT LOGIC ---
async def run_bot(browser, bot_id, pin, base_name):
    context = await browser.new_context()
    page = await context.new_page()
    # Turbo mode: stop images/styles
    await page.route("**/*", lambda route: route.abort() 
        if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
        else route.continue_())
    try:
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=20000)
        await page.fill("#nickname", f"{base_name}{bot_id}")
        await page.keyboard.press("Enter")
        return True
    except:
        return False

async def start_load_test():
    # Tell Playwright to look in our custom folder
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "./pw-browser"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        for i in range(1, count + 1):
            asyncio.create_task(run_bot(browser, i, pin, name))
            progress.progress(i / count)
            status.info(f"Bots joining: {i}/{count}")
            await asyncio.sleep(delay)
            
        status.success(f"Successfully launched {count} bots!")
        await asyncio.sleep(600) # Keep them alive for 10 mins
        await browser.close()

if st.button("Start Bots"):
    if pin:
        asyncio.run(start_load_test())
    else:
        st.error("Enter a PIN!")
