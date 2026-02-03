import streamlit as st
import asyncio
from kahoot import client

# --- UI SETUP ---
st.set_page_config(page_title="Lightning Kahoot", page_icon="⚡")
st.title("⚡ Lightning Kahoot Joiner")
st.info("This version uses raw API packets (No Browser) for maximum speed.")

with st.sidebar:
    pin = st.text_input("Game PIN", placeholder="123456")
    base_name = st.text_input("Username prefix", value="Bot")
    bot_count = st.slider("Number of Bots", 1, 50, 20)

status_area = st.empty()

# --- BOT LOGIC ---
def bot_join(bot_id, pin, name):
    bot = client()
    # join() is synchronous in this library, so it's very fast
    bot.join(pin, f"{name}{bot_id}")
    return bot

def start_attack():
    status_area.warning(f"🚀 Launching {bot_count} bots...")
    bots = []
    
    for i in range(1, bot_count + 1):
        try:
            new_bot = bot_join(i, pin, base_name)
            bots.append(new_bot)
            status_area.text(f"✅ Bot {i} joined!")
        except Exception as e:
            st.error(f"Bot {i} failed: {e}")
            break
            
    status_area.success(f"🔥 {len(bots)} bots joined the lobby!")
    # Keep the bots alive
    st.session_state['active_bots'] = bots

# --- EXECUTION ---
if st.button("Launch Lightning Attack"):
    if pin:
        start_attack()
    else:
        st.error("Enter a PIN!")
