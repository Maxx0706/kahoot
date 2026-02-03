import streamlit as st
import asyncio
import random
from playwright.async_api import async_playwright

# --- UI SETUP ---
st.set_page_config(page_title="Ghost Buster", page_icon="👻")
st.title("👻 Kahoot Ghost-Buster")

pin = st.sidebar.text_input("Game PIN")
name = st.sidebar.text_input("Name", value="Guest")
count = st.sidebar.slider("Bots", 1, 10, 3)

# --- STEALTH ENGINE ---
async def join_lobby(browser, i, pin, name):
    # Use a persistent context to make it look like a returning user
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        viewport={'width': 1366, 'height': 768},
        device_scale_factor=1,
    )
    
    # Inject stealth script to hide 'headless' nature
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    """)
    
    page = await context.new_page()
    try:
        # Commit ensures we don't wait for heavy tracking scripts to load
        await page.goto(f"https://kahoot.it/?pin={pin}", wait_until="domcontentloaded")
        
        # Human-like typing
        await page.wait_for_selector("#nickname", timeout=10000)
        await page.click("#nickname")
        await page.type("#nickname", f"{name}{i}", delay=random.randint(100, 200))
        
        await asyncio.sleep(random.uniform(0.5, 1.5))
        await page.keyboard.press("Enter")
        
        # Keep tab alive for 5 minutes
        await asyncio.sleep(300)
    except Exception as e:
        print(f"Bot {i} failed: {e}")
    finally:
        await context.close()

async def start_run():
    async with async_playwright() as p:
        # DO NOT use --single-process here; it's a bot flag
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        
        st.info(f"🚀 Deploying {count} stealth bots...")
        tasks = []
        for i in range(1, count + 1):
            tasks.append(asyncio.create_task(join_lobby(browser, i, pin, name)))
            # CRITICAL: 2.5s delay makes it look like real people joining one by one
            await asyncio.sleep(2.5) 
            
        await asyncio.gather(*tasks)
        await browser.close()

if st.button("GO LIVE"):
    if pin:
        asyncio.run(start_run())
    else:
        st.error("PIN is empty!")
