import streamlit as st
import asyncio
import os
import subprocess
import sys
import random
from playwright.async_api import async_playwright
# --- NEW IMPORT SYNTAX ---
from playwright_stealth import Stealth

# --- 1. SETUP ---
@st.cache_resource
def install_playwright():
    try:
        # We need to install the browser binaries
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Installation failed: {e}")
        return False

is_ready = install_playwright()

# --- 2. UI ---
st.set_page_config(page_title="Kahoot Flash", page_icon="⚡")
st.title("⚡ Kahoot Flash Joiner")

with st.sidebar:
    pin = st.text_input("Game PIN")
    name = st.text_input("Username", value="Player")
    count = st.slider("Bots", 1, 10, 5)

# --- 3. THE ENGINE ---
async def join_bot(i, pin, base_name):
    # Recommended usage for playwright-stealth 2.0.0:
    # We apply stealth to the entire playwright instance using the 'use_async' method
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--single-process"]
        )
        
        # All pages created from this 'p' instance will have stealth applied automatically
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Join Logic
            await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_selector("#nickname", timeout=10000)
            await page.fill("#nickname", f"{base_name}{i}{random.randint(10,99)}")
            await page.keyboard.press("Enter")
            
            # Stay active
            await asyncio.sleep(600)
        except:
            pass
        finally:
            await browser.close()

async def run_attack():
    st.info(f"🚀 Launching {count} bots...")
    tasks = [join_bot(i, pin, name) for i in range(1, count + 1)]
    await asyncio.gather(*tasks)

if st.button("START"):
    if pin and is_ready:
        asyncio.run(run_attack())
    else:
        st.error("Wait for boot or enter PIN.")
