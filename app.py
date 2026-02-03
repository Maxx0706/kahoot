import streamlit as st
import asyncio
import os
import subprocess
import sys
from playwright.async_api import async_playwright

# --- 1. THE INSTALLER ---
@st.cache_resource
def install_playwright():
    """Installs the browser binaries. System deps must be in packages.txt"""
    try:
        # We only install chromium to save space and time
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Browser installation failed: {e}")
        return False

# Start installation on app boot
browser_installed = install_playwright()

# --- 2. UI SETUP ---
st.set_page_config(page_title="Kahoot Loader", page_icon="🚀")
st.title("🚀 Kahoot Load Tester")

with st.sidebar:
    st.header("Settings")
    pin = st.text_input("Kahoot Game PIN", placeholder="123456")
    name = st.text_input("Base Username", value="Bot")
    count = st.slider("Bot Count", 1, 25, 10)
    delay = st.slider("Join Delay (sec)", 0.1, 1.0, 0.3)

status_area = st.empty()
progress_bar = st.progress(0)

# --- 3. BOT LOGIC ---
async def run_bot(browser, bot_id, pin, base_name):
    """Function for a single bot to join the game"""
    context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    page = await context.new_page()
    
    # Disable heavy assets to save RAM
    await page.route("**/*", lambda route: route.abort() 
        if route.request.resource_type in ["image", "media", "font"] 
        else route.continue_())
    
    try:
        # Navigate to Kahoot
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="networkidle", timeout=20000)
        
        # Join logic
        await page.wait_for_selector("#nickname", timeout=10000)
        await page.fill("#nickname", f"{base_name}{bot_id}")
        await page.keyboard.press("Enter")
        
        # Keep alive for 10 mins
        await asyncio.sleep(600) 
    except Exception:
        pass
    finally:
        await context.close()

async def start_load_test():
    """Main controller for the load test"""
    if not browser_installed:
        st.error("Browser not ready. Please refresh the page.")
        return

    async with async_playwright() as p:
        status_area.warning("Initializing Chromium...")
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox", 
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage", 
                "--disable-gpu",
                "--single-process"
            ]
        )
        
        tasks = []
        for i in range(1, count + 1):
            # Queue the bot join
            task = asyncio.create_task(run_bot(browser, i, pin, name))
            tasks.append(task)
            
            # Update UI
            progress_bar.progress(i / count)
            status_area.info(f"🚀 Bot {i}/{count} joining...")
            await asyncio.sleep(delay)
        
        status_area.success(f"✅ All {count} bots are active!")
        # Keep the main process open so bots don't die
        await asyncio.gather(*tasks)
        await browser.close()

# --- 4. THE EXECUTION ---
if st.button("Start Bots"):
    if pin:
        # Create a clean loop for this session
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(start_load_test())
        except Exception as e:
            st.error(f"Execution Error: {e}")
        finally:
            loop.close()
    else:
        st.error("Please enter a PIN!")
