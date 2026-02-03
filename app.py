import streamlit as st
import asyncio
import random
import os
import subprocess
import sys
from playwright.async_api import async_playwright

# --- 1. SYSTEM INITIALIZATION ---
@st.cache_resource
def install_playwright():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Binary install failed: {e}")
        return False

is_ready = install_playwright()

# --- 2. UI DESIGN ---
st.set_page_config(page_title="Flash Bot", page_icon="⚡")
st.title("⚡ Flash Stealth Joiner")

with st.sidebar:
    st.header("Settings")
    pin = st.text_input("Game PIN", placeholder="123456")
    base_name = st.text_input("Username", value="Player")
    bot_count = st.sidebar.slider("Bots", 1, 20, 10)
    # We use a small delay to avoid TargetClosedError
    join_delay = st.sidebar.slider("Join Interval (sec)", 0.2, 1.0, 0.4)

status_area = st.empty()
progress_bar = st.progress(0)

# --- 3. THE LIGHTNING ENGINE ---
async def join_sequence(browser, i, pin, name):
    """High-speed stealth join using minimal RAM"""
    context = None
    try:
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={'width': 800, 'height': 600}
        )
        
        # Disable automation detection
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        page = await context.new_page()
        
        # SPEED: Block images and fonts
        await page.route("**/*", lambda r: r.abort() 
            if r.request.resource_type in ["image", "font", "media"] 
            else r.continue_())
        
        # Navigate and Join
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_selector("#nickname", timeout=5000)
        
        # Type name and Enter
        await page.fill("#nickname", f"{name}{i}{random.randint(10,99)}")
        await page.keyboard.press("Enter")
        
        # Keep connection alive in background
        await asyncio.sleep(600) 
        
    except Exception:
        pass # Allow individual bots to fail without crashing the app

async def launch_attack():
    if not is_ready:
        st.error("Playwright not ready.")
        return

    async with async_playwright() as p:
        status_area.warning("Initializing Flash Engine...")
        
        # LAUNCH ARGS: Optimized for low-RAM servers
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process" # Keeps all tabs in one process to save RAM
            ]
        )
        
        tasks = []
        for i in range(1, bot_count + 1):
            # Create the task but don't 'await' it yet
            task = asyncio.create_task(join_sequence(browser, i, pin, base_name))
            tasks.append(task)
            
            # UI Updates
            progress_bar.progress(i / bot_count)
            status_area.info(f"⚡ Deploying Bot {i}...")
            
            # The 'Sweet Spot' delay to prevent TargetClosedError
            await asyncio.sleep(join_delay)
        
        status_area.success(f"🔥 {bot_count} bots are currently joining!")
        # Wait for all background tasks to finish their sleep
        await asyncio.gather(*tasks)
        await browser.close()

# --- 4. EXECUTION ---
if st.button("EXECUTE FLASH JOIN"):
    if pin:
        # Create a fresh event loop for the button click
        try:
            asyncio.run(launch_attack())
        except Exception as e:
            st.error(f"System Overload: {e}")
            st.info("Try increasing the 'Join Interval' in the sidebar.")
    else:
        st.error("PIN Required")
