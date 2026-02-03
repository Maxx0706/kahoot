import streamlit as st
import asyncio
import os
import subprocess
import sys
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- 1. CLEANUP & INSTALL (Fixes the "Oven" Issue) ---
@st.cache_resource
def prepare_environment():
    try:
        # Kill any zombie chrome processes from previous crashes
        os.system("pkill -9 chrome || true")
        os.system("pkill -9 chromium || true")
        
        # Install Chromium
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Boot error: {e}")
        return False

is_ready = prepare_environment()

# --- 2. UI ---
st.set_page_config(page_title="Final Flash", page_icon="⚡")
st.title("⚡ Final Flash Joiner")

pin = st.sidebar.text_input("PIN")
name = st.sidebar.text_input("Name", value="Bot")
count = st.sidebar.slider("Bots", 1, 8, 4) # Lower count = more stability

# --- 3. THE ENGINE ---
async def join_bot(browser, i, pin, base_name):
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    await stealth_async(page)
    
    try:
        # Speed: Block heavy media
        await page.route("**/*", lambda r: r.abort() if r.request.resource_type in ["image", "media", "font"] else r.continue_())
        
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=20000)
        await page.wait_for_selector("#nickname", timeout=10000)
        await page.fill("#nickname", f"{base_name}_{i}")
        await page.keyboard.press("Enter")
        await asyncio.sleep(300) 
    except:
        pass
    finally:
        await context.close()

async def run_attack():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process"]
        )
        tasks = [join_bot(browser, i, pin, name) for i in range(1, count + 1)]
        st.success(f"🚀 Deploying {count} bots...")
        await asyncio.gather(*tasks)
        await browser.close()

if st.button("START"):
    if pin and is_ready:
        asyncio.run(run_attack())
    else:
        st.error("Check PIN or wait for boot.")
