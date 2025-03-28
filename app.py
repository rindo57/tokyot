import os
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

# Bot setup
api_id = "10247139"  # Get from https://my.telegram.org
api_hash = "96b46175824223a33737657ab943fd6a"  # Get from https://my.telegram.org
bot_token = "8090184780:AAGUEdPYHK00usmhf-46GW0t5mPO2pztsaM"# Get from @BotFather

app = Client("anime_search_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Global dictionary to store user search data
user_data = {}

def extract_main_links(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    anime_data = []

    for td in soup.find_all("td", class_=["c_h2", "c_h2b"]):
        a_tag = td.find("a", href=True)
        if a_tag and a_tag.text.strip():  # Ensure title is not empty
            title = a_tag.text.strip()
            full_url = urljoin(url, a_tag["href"])
            anime_data.append((title, full_url))

    return anime_data

def create_results_message(results, start_idx=0):
    message_text = "**Search Results:**\n\n"
    end_idx = min(start_idx + 5, len(results))
    
    for i in range(start_idx, end_idx):
        title, url = results[i]
        url+=")"
        message_text += f"{i+1}. [{title}]({url})\n"
    
    return message_text, end_idx

def create_pagination_buttons(results, current_page):
    keyboard = []
    total_pages = (len(results) + 4) // 5  # Calculate total pages (ceil division)
    
    if current_page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_{current_page}"))
    
    if (current_page + 1) * 5 < len(results):
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{current_page}"))
    
    return InlineKeyboardMarkup([keyboard]) if keyboard else None

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text(
        "👋 Hello! I'm an anime search bot.\n\n"
        "Just send me the name of an anime you're looking for, "
        "and I'll search for it on Tokyo Insider!"
    )

@app.on_message(filters.text & ~filters.command("start"))
async def search_anime(client: Client, message: Message):
    query = message.text.strip()
    if not query:
        return await message.reply_text("Please enter a search query.")
    
    # Create search URL
    search_term = quote(query.replace(" ", "_").lower())
    search_url = f"https://www.tokyoinsider.com/anime/search?k={search_term}"
    
    try:
        results = extract_main_links(search_url)
        if not results:
            return await message.reply_text("No results found for your query.")
        
        # Store results in user_data for pagination
        user_data[message.from_user.id] = {
            "results": results,
            "current_page": 0
        }
        
        # Create and send first page of results
        message_text, _ = create_results_message(results)
        reply_markup = create_pagination_buttons(results, 0)
        
        await message.reply_text(
            message_text,
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        print(f"Error: {e}")
        await message.reply_text("An error occurred while searching. Please try again later.")

@app.on_callback_query()
async def handle_pagination(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    
    if user_id not in user_data:
        return await callback_query.answer("Your search session has expired. Please search again.")
    
    results = user_data[user_id]["results"]
    current_page = user_data[user_id]["current_page"]
    
    if data.startswith("next_"):
        new_page = int(data.split("_")[1]) + 1
    elif data.startswith("prev_"):
        new_page = int(data.split("_")[1]) - 1
    else:
        return await callback_query.answer()
    
    # Update current page
    user_data[user_id]["current_page"] = new_page
    
    # Create new message and buttons
    start_idx = new_page * 5
    message_text, _ = create_results_message(results, start_idx)
    reply_markup = create_pagination_buttons(results, new_page)
    
    # Edit the message with new content
    await callback_query.message.edit_text(
        message_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True
    )
    
    await callback_query.answer()

if __name__ == "__main__":
    print("Bot started...")
    app.run()
