import streamlit as st
import asyncio
import os
import subprocess
import sys
from playwright.async_api import async_playwright

# --- 1. THE INSTALLER (Runs when the app boots) ---
@st.cache_resource
def install_playwright():
    st.info("Checking browser environment...")
    # This installs chromium into the standard location
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install-deps"], check=True)
    return True

# Trigger the install
installed = install_playwright()

# --- 2. UI SETUP ---
st.set_page_config(page_title="Kahoot Loader", page_icon="🚀")
st.title("🚀 Kahoot Load Tester")

with st.sidebar:
    pin = st.text_input("Kahoot Game PIN", placeholder="123456")
    name = st.text_input("Base Username", value="Bot")
    count = st.slider("Bot Count", 1, 20, 10)
    delay = st.slider("Join Delay (sec)", 0.1, 1.0, 0.3)

status_area = st.empty()
progress_bar = st.progress(0)

# --- 3. BOT LOGIC ---
async def run_bot(browser, bot_id, pin, base_name):
    try:
        context = await browser.new_context()
        page = await context.new_page()
        # Block heavy assets to save RAM
        await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_())
        
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector("#nickname", timeout=5000)
        await page.fill("#nickname", f"{base_name}{bot_id}")
        await page.keyboard.press("Enter")
        # Keep the bot alive in the background
        await asyncio.sleep(600) 
    except:
        pass

async def start_load_test():
    async with async_playwright() as p:
        status_area.warning("Launching Chromium...")
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        
        for i in range(1, count + 1):
            # Create task so bots run concurrently
            asyncio.create_task(run_bot(browser, i, pin, name))
            progress_bar.progress(i / count)
            status_area.info(f"Bot {i}/{count} joining...")
            await asyncio.sleep(delay)
        
        status_area.success(f"✅ All {count} bots requested to join!")
        # Keep the main process alive so the browser doesn't close
        await asyncio.sleep(600) 
        await browser.close()

# --- 4. EXECUTION ---
if st.button("Start Bots"):
    if pin:
        try:
            # Standard asyncio run is fine if we handle the loop properly
            asyncio.run(start_load_test())
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.error("Please enter a PIN!")
