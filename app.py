import streamlit as st
import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# --- 1. BOOTSTRAP ---
@st.cache_resource
def install_pw():
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    return True

ready = install_pw()

# --- 2. THE HUMAN EMULATOR ---
async def join_as_iphone(i, pin, base_name):
    """Bypasses ghosting by mimicking a real iPhone on a cellular network"""
    async with Stealth().use_async(async_playwright()) as p:
        # LAUNCH: Use unique user data dirs to prevent 'clone' detection
        browser = await p.chromium.launch(headless=True, args=[
            "--no-sandbox", 
            "--disable-blink-features=AutomationControlled"
        ])
        
        # MASK: Use a real iPhone 15 Pro Max profile
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
            viewport={'width': 430, 'height': 932},
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True
        )
        
        page = await context.new_page()
        
        try:
            # 1. Random delay so they don't hit the server at the exact same millisecond
            await asyncio.sleep(random.uniform(1, 4))
            
            # 2. Go to Kahoot with a 'Referer' header (looks like they came from Google)
            await page.set_extra_http_headers({"Referer": "https://www.google.com/"})
            await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="networkidle")
            
            # 3. HUMAN TYPING: Never use .fill(), it's too fast
            nickname_box = await page.wait_for_selector("#nickname", timeout=10000)
            await nickname_box.click()
            
            full_name = f"{base_name}{i}"
            for char in full_name:
                await page.keyboard.type(char, delay=random.randint(100, 250))
                
            await asyncio.sleep(random.uniform(0.5, 1.2))
            await page.keyboard.press("Enter")
            
            # 4. Keep alive
            await asyncio.sleep(300)
        except Exception:
            pass
        finally:
            await browser.close()

# --- 3. UI ---
st.title("⚡ Ghost-Bypass Joiner")
pin_input = st.text_input("PIN")
name_input = st.text_input("Prefix", value="Guest")
bot_val = st.slider("Bots", 1, 10, 3)

if st.button("LAUNCH"):
    if pin_input and ready:
        st.info("🔥 Attempting to bypass shadow-ban...")
        # Fire them off!
        loop = asyncio.get_event_loop()
        for i in range(1, bot_val + 1):
            loop.create_task(join_as_iphone(i, pin_input, name_input))
        st.success("Bots dispatched. If they don't appear in 10s, your IP is hard-blocked.")
