import streamlit as st
import asyncio
import random
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# --- UI ---
st.set_page_config(page_title="Human Bot", page_icon="👤")
st.title("👤 Human-Emulated Kahoot Joiner")

with st.sidebar:
    pin = st.text_input("Game PIN")
    name = st.text_input("Username", value="Player")
    count = st.slider("Bots", 1, 5, 3) # Keep it low to avoid IP flags

# --- THE HUMAN ENGINE ---
async def join_humanly(browser, i, pin, name):
    # Create a unique context for every single bot
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        viewport={'width': 390, 'height': 844}, # Look like an iPhone
        is_mobile=True,
        has_touch=True
    )
    
    page = await context.new_page()
    # Apply advanced stealth patterns
    await stealth_async(page)
    
    try:
        # 1. Random delay before starting (don't all join at once)
        await asyncio.sleep(random.uniform(2, 5))
        
        # 2. Go to site
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="networkidle")
        
        # 3. Simulate "Human Thinking" before typing
        await asyncio.sleep(random.uniform(1, 3))
        
        # 4. Type nickname slowly with mistakes and backspaces (emulated)
        await page.wait_for_selector("#nickname", timeout=10000)
        await page.click("#nickname")
        nickname = f"{name}{i}"
        for char in nickname:
            await page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # 5. Press Enter and wait
        await asyncio.sleep(0.5)
        await page.keyboard.press("Enter")
        
        # Keep connection for 10 minutes
        await asyncio.sleep(600)
        
    except Exception as e:
        print(f"Bot {i} failed: {e}")
    finally:
        await context.close()

async def run_attack():
    async with async_playwright() as p:
        # Force a real-looking browser launch
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        st.info(f"🚀 Deploying {count} humanized bots...")
        tasks = []
        for i in range(1, count + 1):
            tasks.append(asyncio.create_task(join_humanly(browser, i, pin, name)))
            # STAGGER: Wait 5-10 seconds between each bot to look natural
            await asyncio.sleep(random.uniform(5, 10))
            
        await asyncio.gather(*tasks)
        await browser.close()

if st.button("RUN HUMANIZED JOIN"):
    if pin:
        asyncio.run(run_attack())
    else:
        st.error("Enter a PIN!")
