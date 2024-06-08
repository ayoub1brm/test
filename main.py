import threading
import os
import subprocess
from discord_bot.discord_bot import setup_discord_bot
from database.database import Database

discord_token = os.getenv('DISCORD_TOKEN')

def run_streamlit():
    os.system('streamlit run app.py')

def run_discord_bot():
    setup_discord_bot(discord_token)

if __name__ == "__main__":
    # Run Streamlit app in a separate thread
    streamlit_thread = threading.Thread(target=run_streamlit)
    streamlit_thread.start()

    # Run Discord bot
    run_discord_bot()
