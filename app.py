import streamlit as st
import asyncio
import os
import subprocess
import sys
from playwright.async_api import async_playwright

# --- 1. SYSTEM INITIALIZATION ---
@st.cache_resource
def install_playwright():
    """Download Chromium binary. System libs must be in packages.txt"""
    try:
        # We only install chromium-headless-shell to save space
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Binary install failed: {e}")
        return False

# Run installer once on boot
is_ready = install_playwright()

# --- 2. UI DESIGN ---
st.set_page_config(page_title="Kahoot Botter", page_icon="⚡")
st.title("⚡ Kahoot Load Tester")
st.caption("Optimized for Streamlit Cloud (1GB RAM Limit)")

with st.sidebar:
    st.header("Configuration")
    game_pin = st.text_input("Game PIN", placeholder="e.g. 123456")
    base_name = st.text_input("Username prefix", value="Bot")
    bot_count = st.slider("Number of Bots", 1, 15, 5)
    join_delay = st.slider("Delay between joins (sec)", 0.5, 3.0, 1.2)

status = st.empty()
progress = st.progress(0)

# --- 3. BOT CORE LOGIC ---
async def spawn_bot(browser, bot_id, pin, name):
    """Memory-efficient bot instance"""
    context = None
    try:
        # Create a tiny viewport to save GPU/RAM resources
        context = await browser.new_context(
            viewport={'width': 100, 'height': 100},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        # AGGRESSIVE BLOCKING: Do not load images, CSS, or fonts
        await page.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
            else route.continue_())

        # Navigate to Kahoot
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=20000)
        
        # Enter Nickname
        await page.wait_for_selector("#nickname", timeout=10000)
        await page.fill("#nickname", f"{name}_{bot_id}")
        await page.keyboard.press("Enter")
        
        # Keep connection alive (Kahoot needs the socket open)
        await asyncio.sleep(600) 
        
    except Exception:
        pass # Silently fail individual bots to keep the rest running
    finally:
        if context:
            await context.close()

async def run_load_test():
    """Manager to handle the browser lifecycle"""
    if not is_ready:
        st.error("Playwright is not initialized.")
        return

    async with async_playwright() as p:
        status.warning("Launching lightweight browser...")
        # CRITICAL FLAGS for low RAM (Streamlit Cloud)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage", # Uses /tmp instead of shared memory
                "--single-process",        # Forces all tabs into one process
                "--disable-gpu",
                "--no-zygote"
            ]
        )

        tasks = []
        for i in range(1, bot_count + 1):
            # Start bot as a background task
            task = asyncio.create_task(spawn_bot(browser, i, game_pin, base_name))
            tasks.append(task)
            
            # UI Updates
            progress.progress(i / bot_count)
            status.info(f"🚀 Deploying Bot {i} of {bot_count}...")
            
            # Sequential join prevents RAM spikes
            await asyncio.sleep(join_delay)

        status.success(f"✅ {bot_count} bots successfully dispatched!")
        # Wait for all bots to finish their sleep cycle
        await asyncio.gather(*tasks)
        await browser.close()

# --- 4. EXECUTION ---
if st.button("🚀 Start Load Test"):
    if not game_pin:
        st.error("Please enter a Game PIN!")
    else:
        # Use a fresh event loop to prevent 'Loop already running' errors
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_load_test())
        except Exception as e:
            st.error(f"Critical System Failure: {e}")
        finally:
            loop.close()
