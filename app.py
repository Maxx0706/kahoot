import streamlit as st
import asyncio
from playwright.async_api import async_playwright

st.set_page_config(page_title="Kahoot Loader", page_icon="🚀")
st.title("🚀 Kahoot Load Tester")

# UI Elements in the Sidebar or Main Page
pin = st.text_input("Kahoot Game PIN", placeholder="123456")
name = st.text_input("Base Username", value="Bot")
count = st.number_input("Bot Count", min_value=1, max_value=50, value=10) # Limited for free servers
delay = st.slider("Join Delay (seconds)", 0.1, 2.0, 0.3)

async def run_bot(browser, bot_id, pin, base_name):
    context = await browser.new_context()
    page = await context.new_page()
    await page.route("**/*", lambda route: route.abort() 
        if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
        else route.continue_())
    try:
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded")
        await page.fill("#nickname", f"{base_name}{bot_id}")
        await page.keyboard.press("Enter")
        return True
    except:
        return False

async def start_load_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(1, count + 1):
            asyncio.create_task(run_bot(browser, i, pin, name))
            progress_bar.progress(i / count)
            status_text.text(f"Bots joining: {i}/{count}")
            await asyncio.sleep(delay)
        
        status_text.success(f"✅ {count} bots launched!")
        await asyncio.sleep(600) # Keep browser alive

if st.button("Start Bots"):
    if pin:
        asyncio.run(start_load_test())
    else:
        st.error("Please enter a PIN!")
