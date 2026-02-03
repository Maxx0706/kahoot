import streamlit as st
import asyncio
import os
import subprocess
from playwright.async_api import async_playwright

# --- 1. SETUP & BROWSER INSTALLATION ---
# This part ensures the browser exists on the server
if not os.path.exists("/home/appuser/.cache/ms-playwright"):
    try:
        subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
        subprocess.run(["python", "-m", "playwright", "install-deps"], check=True)
    except:
        pass

# --- 2. UI SETUP ---
st.set_page_config(page_title="Kahoot Loader", page_icon="🚀")
st.title("🚀 Kahoot Load Tester")

pin = st.text_input("Kahoot Game PIN", placeholder="123456")
name = st.text_input("Base Username", value="Bot")
count = st.slider("Bot Count", 1, 20, 10)
delay = st.slider("Join Delay (seconds)", 0.1, 1.0, 0.3)

status_area = st.empty()
progress_bar = st.progress(0)

# --- 3. BOT LOGIC ---
async def run_bot(browser, bot_id, pin, base_name):
    context = await browser.new_context()
    page = await context.new_page()
    # Disable images/css to save RAM
    await page.route("**/*", lambda route: route.abort() 
        if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
        else route.continue_())
    try:
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=15000)
        await page.fill("#nickname", f"{base_name}{bot_id}")
        await page.keyboard.press("Enter")
        return True
    except:
        return False

async def start_load_test():
    async with async_playwright() as p:
        # Launch with essential server flags
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        
        success = 0
        for i in range(1, count + 1):
            # Launch bots as background tasks
            asyncio.create_task(run_bot(browser, i, pin, name))
            success += 1
            progress_bar.progress(i / count)
            status_area.info(f"Bots joining: {i}/{count}")
            await asyncio.sleep(delay)
        
        status_area.success(f"✅ {success} bots launched! Keeping them alive...")
        await asyncio.sleep(600) # Keep browser open for 10 minutes
        await browser.close()

# --- 4. THE FIX FOR THE CRASH ---
if st.button("Start Bots"):
    if pin:
        # We wrap the async call in a way that doesn't conflict with Streamlit
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_load_test())
        finally:
            loop.close()
    else:
        st.error("Please enter a PIN!")
