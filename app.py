import os
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
import requests
from base64 import standard_b64encode, standard_b64decode
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

# Bot setup
api_id = "10247139"  # Get from https://my.telegram.org
api_hash = "96b46175824223a33737657ab943fd6a"  # Get from https://my.telegram.org
bot_token = "8090184780:AAGUEdPYHK00usmhf-46GW0t5mPO2pztsaM"# Get from @BotFather

app = Client("anime_search_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Global dictionary to store user search data
user_data = {}

def b64_to_str(b64: str) -> str:
    bytes_b64 = b64.encode('ascii')
    bytes_str = standard_b64decode(bytes_b64)
    __str = bytes_str.decode('ascii')
    return __str
    
def str_to_b64(__str: str) -> str:
    str_bytes = __str.encode('ascii')
    bytes_b64 = standard_b64encode(str_bytes)
    b64 = bytes_b64.decode('ascii')
    return b64


def extract_episode_links(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    anime_data = []

    for td in soup.find_all("div", class_=["episode c_h2", "episode c_h2b"]):
        a_tag = td.find("a", href=True)
        if a_tag and a_tag.text.strip():  # Ensure title is not empty
            title = a_tag.text.strip()
            if title.startswith("upload"):
                pass
            else:
            # Check for episode subtitle in the i tag
                i_tag = td.find("i")
                if i_tag:
                    subtitle = i_tag.text.strip()
                    if subtitle.startswith(":"):
                        subtitle = subtitle[1:].strip()
                    title = f"{title} - {subtitle}"
                full_url = urljoin(url, a_tag["href"])
                anime_data.append((title, full_url))

    return anime_data


def extract_download_links(url):
    # Send a GET request to the URL
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad status codes
    
    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all download entries (they alternate between c_h2 and c_h2b classes)
    download_entries = soup.find_all(class_=['c_h2', 'c_h2b'])
    
    results = []
    
    for entry in download_entries:
        # Extract title and download link - now we'll specifically get the main link, not the comments link
        main_div = entry.find('div')  # Get the first div inside the entry
        download_link_tag = main_div.find('a', href=lambda x: x and not x.endswith('/comment'))
        
        if not download_link_tag:
            continue  # Skip if no download link found
            
        title = download_link_tag.text.strip()
        download_link = download_link_tag['href']
        
        # Make sure the link is absolute
        if not download_link.startswith('http'):
            download_link = f"https://www.tokyoinsider.com{download_link}"
        
        # Extract file info
        finfo = entry.find(class_='finfo')
        
        # Extract language (class of the first span)
        language_span = finfo.find('span')
        language = language_span['class'][0] if language_span and language_span.has_attr('class') else "N/A"
        
        # Extract size, downloads, uploader, and added date
        info_text = finfo.get_text(separator='|').split('|')
        info = [item.strip() for item in info_text if item.strip()]
        
        size = "N/A"
        added_on = "N/A"
        
        for i, item in enumerate(info):
            if item.startswith('Size:'):
                size = info[i+1] if i+1 < len(info) else "N/A"
            elif item.startswith('Added On:'):
                added_on = info[i+1] if i+1 < len(info) else "N/A"
        
        results.append({
            'title': title,
            'download_link': download_link,
            'size': size,
            'language': language,
            'added_on': added_on
        })
    
    return results
'''
# URL to scrape
url = "https://www.tokyoinsider.com/anime/O/One_Outs_(TV)/episode/20"

# Extract and print the information
episode_info = extract_episode_info(url)

for idx, info in enumerate(episode_info, 1):
    print(f"Entry {idx}:")
    print(f"Title: {info['title']}")
    print(f"Download Link: {info['download_link']}")
    print(f"File Size: {info['size']}")
    print(f"Language: {info['language']}")
    print(f"Added On: {info['added_on']}")
    print("-" * 50)
'''
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
    
    message_text = "<b>Search Results:</b>\n\n"
    end_idx = min(start_idx + 25, len(results))
    
    for i in range(start_idx, end_idx):
        title, url = results[i]
        url = url.replace("https://www.tokyoinsider.com/anime/", "")
        url = url.replace("https://tokyoinsider.com/anime/", "")
        nurl = url.replace("/", "=").replace(":", "ies").replace("(TV)", "TV").replace(".", "lluf").replace(",", "dsj").replace("!", "wq").replace("(Movie)", "eiv").replace("(OVA)", "OVA").replace("(Specials)", "Specials").replace("(ONA)", "ONA").replace("Kingdom", "gni").replace("(movie)","vom")
        nurl = nurl.replace("(","lx").replace(")","rx")                                                                                                                                                                                                                                                      
                                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                               
                                                                                                                                                                                                                                                               

        xurl = "https://t.me/animeddlbot?start="+nurl
        message_text += f"{i+1}. <a href='{xurl}'>{title}</a>\n"
    
    return message_text, end_idx

def create_ep_results_message(results, start_idx=0):
    message_text = "<b>Search Results:</b>\n\n"
    end_idx = min(start_idx + 25, len(results))
    
    for i in range(start_idx, end_idx):
        title, url = results[i]
        url = url.replace("https://www.tokyoinsider.com/anime/", "")
        url = url.replace("https://tokyoinsider.com/anime/", "")
        nurl = url.replace("/", "=").replace(":", "ies").replace("(TV)", "TV").replace(".", "lluf").replace(",", "dsj").replace("!", "wq").replace("(Movie)", "eiv").replace("(OVA)", "OVA").replace("(Specials)", "Specials").replace("(ONA)", "ONA").replace("Kingdom", "gni").replace("(movie)", "vom")
        nurl=nurl.replace("(","lx").replace(")","rx")
        
        yurl = nurl.replace("=movie", "=m").replace("Movie_1", "1M").replace("Movie_2", "2M").replace("Movie_3", "3M").replace("Movie_4", "4M").replace("Movie_5", "5M").replace("Movie_6", "6M")

        print("ep nurl: ", yurl)
        
        xurl = "https://t.me/animeddlbot?start="+yurl
        message_text += f"{i+1}. <a href='{xurl}'>{title}</a>\n"
    
    return message_text, end_idx

def create_dl_results_message(results):
    print(results)
    message_text = "<b>Download Links:</b>\n\n"
    for idx, info in enumerate(results, 1):
        language = info['language']
        language = language.replace("lang_en", "🇬🇧")
        download_link = info['download_link']
        download_link = download_link.replace("media.tokyoinsider.com:8080", "f69.ddlserverv1.me.in")
        message_text += f"<blockquote><a href='{download_link}'><b>{info['title']}</b></a>\n{language} | {info['size']} | {info['added_on']}</blockquote>\n"
    return message_text

def create_pagination_buttons(results, current_page):
    keyboard = []
    total_pages = (len(results) + 4) // 5  # Calculate total pages (ceil division)
    
    if current_page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"prev_{current_page}"))
    
    if (current_page + 1) * 20 < len(results):
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{current_page}"))
    
    return InlineKeyboardMarkup([keyboard]) if keyboard else None
    
def create_pagination_buttons_ep(results, current_page):
    keyboard = []
    total_pages = (len(results) + 4) // 5  # Calculate total pages (ceil division)
    
    if current_page > 0:
        keyboard.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"epprev_{current_page}"))
    
    if (current_page + 1) * 25 < len(results):
        keyboard.append(InlineKeyboardButton("Next ➡️", callback_data=f"epnext_{current_page}"))
    
    return InlineKeyboardMarkup([keyboard]) if keyboard else None

@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    query = message.text.split(" ", 1)[-1]
    if message.text == "/start":
        await message.reply_text(
            "👋 <b>Hello!</b> I'm an anime search bot.\n\n"
            "Just send me the name of an anime you're looking for, "
            "and I'll search for it on Tokyo Insider!",
            parse_mode=enums.ParseMode.HTML
        )
    elif any(keyword in query for keyword in ["=episode", "=ova", "=m", "=special"]):
        queryx = query.replace("=", "/").replace("ies", ":").replace("TV", "(TV)").replace("lluf", ".").replace("dsj", ",").replace("wq", "!").replace("lx","(").replace("rx",")").replace("eiv", "(Movie)").replace("OVA", "(OVA)").replace("Specials", "(Specials)").replace("ONA", "(ONA)").replace("gni","Kingdom").replace("vom", "(movie)")
        
        queryz = queryx.replace("/m", "/movie").replace("1M", "Movie_1").replace("2M", "Movie_2").replace("3M", "Movie_3").replace("4M", "Movie_4").replace("5M", "Movie_5").replace("6M", "Movie_6")
        dl_url = "https://tokyoinsider.com/anime/"+queryz
        print("dl url ", dl_url)
        try:
            results = extract_download_links(dl_url)
            if not results:
                return await message.reply_text("No results.")
            message_text = create_dl_results_message(results)
        
            await message.reply_text(
                message_text,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
        
        except Exception as e:
            print(f"Error: {e}")
            await message.reply_text("An error occurred while fetchong data. Please try again later.")
    else:
        #equery = b64_to_str(query)
      #  print(equery)
        query = query.replace("=", "/").replace("ies", ":").replace("TV", "(TV)").replace("lluf", ".").replace("dsj", ",").replace("wq", "!").replace("lx","(").replace("rx",")").replace("eiv", "(Movie)").replace("OVA", "(OVA)").replace("Specials", "(Specials)").replace("ONA", "(ONA)").replace("gni","Kingdom").replace("vom", "(movie)")
        ep_url = "https://tokyoinsider.com/anime/"+query
        print(ep_url)
        try:
            results = extract_episode_links(ep_url)
            if not results:
                return await message.reply_text("No results.")
        
        # Store results in user_data for pagination
            user_data[message.from_user.id] = {
                "results": results,
                "current_page": 0
            }
        
        # Create and send first page of results
            message_text, _ = create_ep_results_message(results)
            reply_markup = create_pagination_buttons_ep(results, 0)
        
            await message.reply_text(
                message_text,
                reply_markup=reply_markup,
                disable_web_page_preview=True,
                parse_mode=enums.ParseMode.HTML
            )
        
        except Exception as e:
            print(f"Error: {e}")
            await message.reply_text("An error occurred while fetchong data. Please try again later.")
        

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
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML
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
    
    # Determine pagination type
    if data.startswith("next_") or data.startswith("prev_"):
        prefix = ""
    elif data.startswith("epnext_") or data.startswith("epprev_"):
        prefix = "ep"
    else:
        return await callback_query.answer()

    # Calculate new page
    try:
        direction = 1 if data.startswith(f"{prefix}next_") else -1
        new_page = int(data.split("_")[1]) + direction
    except (ValueError, IndexError):
        return await callback_query.answer("Invalid pagination command.")

    # Update current page
    user_data[user_id]["current_page"] = new_page
    
    # Create new message and buttons based on the prefix
    start_idx = new_page * 25
    if prefix == "ep":
        message_text, _ = create_ep_results_message(results, start_idx)
        reply_markup = create_pagination_buttons_ep(results, new_page)
    else:
        message_text, _ = create_results_message(results, start_idx)
        reply_markup = create_pagination_buttons(results, new_page)

    # Edit the message with new content
    await callback_query.message.edit_text(
        message_text,
        reply_markup=reply_markup,
        disable_web_page_preview=True,
        parse_mode=enums.ParseMode.HTML
    )
    
    await callback_query.answer()


if __name__ == "__main__":
    print("Bot started...")
    app.run()
