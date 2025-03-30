import secrets
import string
import os
from pyrogram import Client, filters, enums
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    Message,
)
import requests
from db import add_user, full_userbase, present_user, del_user, update_user_search_count, get_user_data, add_used_token, add_verification_token, mark_user_verified, is_token_used, mark_token_used, cleanup_expired_tokens, is_valid_verification_token
from base64 import standard_b64encode, standard_b64decode
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import time
from datetime import datetime, timedelta

# Bot setup
api_id = "10247139"  # Get from https://my.telegram.org
api_hash = "96b46175824223a33737657ab943fd6a"  # Get from https://my.telegram.org
bot_token = "8090184780:AAGUEdPYHK00usmhf-46GW0t5mPO2pztsaM"# Get from @BotFather

app = Client("anime_search_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Global dictionary to store user search data
user_data = {}

# Shortener APIs
OUO_API = "https://ouo.press/api/jezWr0hG?s="
NANOLINKS_API = "https://nanolinks.in/api?api=7da8202d8af0c8d76c024a6be6badadaabe66a01&url={}&alias=CustomAlias"

async def get_ouo_shortlink(url):
    try:

        cfurl = "http://localhost:8191/v1"
        headers = {"Content-Type": "application/json"}
        dataz = {
            "cmd": "request.get",
            "url": f"http://ouo.press/api/jezWr0hG?s={url}",
            "maxTimeout": 60000
        }
        responsez = requests.post(cfurl, headers=headers, json=dataz)
        html_content = responsez.json()['solution']['response']
        soup = BeautifulSoup(html_content, 'html.parser')
        ouurl = soup.body.text.strip()
        return ouurl # OUO returns the shortened URL directly
    except Exception as e:
        print(f"OUO Shortener Error: {e}")
        return url  # Fallback to original URL if shortening fails

async def get_nanolinks_shortlink(url):
    try:
        cfurl = "http://localhost:8191/v1"
        headers = {"Content-Type": "application/json"}
        dataz = {
            "cmd": "request.get",
            "url": f"https://nanolinks.in/api?api=7da8202d8af0c8d76c024a6be6badadaabe66a01&url={url}&format=text",
            "maxTimeout": 60000
        }
        responsez = requests.post(cfurl, headers=headers, json=dataz)
        html_content = responsez.json()['solution']['response']
        soup = BeautifulSoup(html_content, 'html.parser')
        ouurl = soup.body.text.strip()
        return nanurl
    
        return nanurl  # Nanolinks returns the shortened URL directly
    except Exception as e:
        print(f"Nanolinks Shortener Error: {e}")
        return url  # Fallback to original URL if shortening fails

def create_verification_buttons(verification_url):
    keyboard = [
        [
            InlineKeyboardButton("OUO (Fast, with ads)", url=verification_url),
            InlineKeyboardButton("Nanolinks (Slower, no ads)", url=verification_url)
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def send_verification_options(client, message, verification_url):
    # Get shortened URLs
    ouo_url = await get_ouo_shortlink(verification_url)
    nano_url = await get_nanolinks_shortlink(verification_url)
    
    # Create buttons with the shortened URLs
    keyboard = [
        [
            InlineKeyboardButton("OUO (Pop-up ads)", url=ouo_url),
            InlineKeyboardButton("Nanolinks (No Pop-up ads)", url=nano_url)
        ]
    ]
    
    await message.reply_text(
        "⚠️ <b>You've reached your daily search limit (5 searches)</b>\n\n"
        "To get more searches (up to 10/day), please verify you're human by completing one of these short links:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=enums.ParseMode.HTML
    )

def generate_verification_token(length=16):
    """Generate a random verification token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


async def check_search_limit(user_id):
    user = await get_user_data(user_id)
    if not user:
        await add_user(user_id, "")
        return True
    
    now = datetime.now()
    last_reset = user.get('last_reset', datetime(1970, 1, 1))
    
    # Reset daily count if it's a new day
    if (now - last_reset) > timedelta(hours=24):
        await update_user_search_count(user_id, 0, now)
        return True
    
    search_count = user.get('search_count', 0)
    verified = user.get('verified', False)
    
    if verified:
        if search_count >= 10:
            return False
    else:
        if search_count >= 5:
            return False
    
    return True
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

mapping = {
    "A-Rank_Party_wo_Ridatsu_shita_Ore_wa,_Moto_Oshiego-tachi_to_Meikyuu_Shinbu_wo_Mezasu_(TV)": "A-Rank",
    "Active_Raid:_Kidou_Kyoushuushitsu_Dai_Hachi_Gakari_2nd_(TV)": "Active_Raid_S2",
    "Akuyaku_Reijou_Level_99:_Watashi_wa_Ura-Boss_desu_ga_Maou_dewa_Arimasen_(TV)": "Akuyaku_Reijou_Level_99",
    "Alice_in_the_Country_of_Hearts:_Wonderful_Wonder_World_(Movie)": "Alice_in_the_Country",
    "Ancien_to_Mahou_no_Tablet:_Mou_Hitotsu_no_Hirune_Hime_(ONA)": "Ancien_to_Mahou",
    "Ane_Log:_Moyako_Neesan_no_Honpen_wo_Tobidashite_Tomaranai_Monologue_(TV)": "Ane_Log",
    "Araiso_Private_High_School_Student_Council_Executive_Committee_(OVA)": "Araiso_Private",
    "Ateuma_Chara_no_Kuse_Shite,_Spadali_Oji_ni_Chouai_Sarete_Imasu_(TV)": "Ateuma_Chara",

    "Bishoujo_Senshi_Sailor_Moon_Crystal:_Death_Busters-hen_(TV)": "Bishoujo_Senshi_Death",
    "Boruto:_Naruto_the_Movie_-_Naruto_ga_Hokage_ni_Natta_Hi_(Special)": "Boruto_Movie_Hokage",
    "Botsuraku_Yotei_no_Kizoku_dakedo,_Hima_datta_kara_Mahou_wo_Kiwametemita_(TV)": "Botsuraku",
    "Boukensha_ni_Naritai_to_Miyako_ni_Deteitta_Musume_ga_S-Rank_ni_Natteta_(TV)": "Boukensha_ni_Naritai",
    "Buddy_Complex:_Kanketsu-hen_-_Ano_Sora_ni_Kaeru_Mirai_de_(Special)": "Buddy_Complex_Special",
    "Buta_no_Gotoki_Sanzoku_ni_Torawarete_Shojo_wo_Ubawareru_Kyonyuu_Himekishi___Onna_Senshi_(TV)": "Buta_no_Gotaku",

    "Cheat_Kusushi_no_Slow_Life:_Isekai_ni_Tsukurou_Drugstore_(TV)": "Cheat_Drugstore",
    "Chiba_Pedal:_Yowamushi_Pedal_to_Manabu_Jitensha_Koutsuu_Anzen_(ONA)": "Chiba_pedal_Anzen",
    "Chiisana_Ahiru_no_Ooki_na_Ai_no_Monogatari:_Ahiru_no_Kwak_(TV)": "Chiisana_Ahiru",
    "Chiisana_Koi_no_Monogatari:_Chichi_to_Sally_Hatsukoi_no_Shiki_(Special)": "Chiisana_Monogatari",
    "Choujin_Koukousei_tachi_wa_Isekai_demo_Yoyuu_de_Ikinuku_you_desu!_(TV)": "Choujin_Koukousei",
    "City_Hunter:_Kinkyuu_Namachuukei!__Kyouakuhan_Saeba_Ryou_no_Saigo_(Special)": "City_hunter_Saeba",
    "Corpse_Party:_Tortured_Souls_-_Bougyakusareta_Tamashii_no_Jukyou_(OVA)": "Corpse_Party_Souls"
}

mappingrev = {
    "A=rank": "A-Rank_Party_wo_Ridatsu_shita_Ore_wa,_Moto_Oshiego-tachi_to_Meikyuu_Shinbu_wo_Mezasu_(TV)",
    "Active_Raid_S2": "Active_Raid:_Kidou_Kyoushuushitsu_Dai_Hachi_Gakari_2nd_(TV)",
    "Akuyaku_Reijou_Level_99": "Akuyaku_Reijou_Level_99:_Watashi_wa_Ura-Boss_desu_ga_Maou_dewa_Arimasen_(TV)",
    "Alice_in_the_Country": "Alice_in_the_Country_of_Hearts:_Wonderful_Wonder_World_(Movie)",
    "Ancien_to_Mahou": "Ancien_to_Mahou_no_Tablet:_Mou_Hitotsu_no_Hirune_Hime_(ONA)",
    "Ane_Log": "Ane_Log:_Moyako_Neesan_no_Honpen_wo_Tobidashite_Tomaranai_Monologue_(TV)",
    "Araiso_Private": "Araiso_Private_High_School_Student_Council_Executive_Committee_(OVA)",
    "Ateuma_Chara": "Ateuma_Chara_no_Kuse_Shite,_Spadali_Oji_ni_Chouai_Sarete_Imasu_(TV)",
    
    "Bishoujo_Senshi_Death": "Bishoujo_Senshi_Sailor_Moon_Crystal:_Death_Busters-hen_(TV)",
    "Boruto_Movie_Hokage": "Boruto:_Naruto_the_Movie_-_Naruto_ga_Hokage_ni_Natta_Hi_(Special)",
    "Botsuraku": "Botsuraku_Yotei_no_Kizoku_dakedo,_Hima_datta_kara_Mahou_wo_Kiwametemita_(TV)",
    "Boukensha_ni_Naritai": "Boukensha_ni_Naritai_to_Miyako_ni_Deteitta_Musume_ga_S-Rank_ni_Natteta_(TV)",
    "Buddy_Complex_Special": "Buddy_Complex:_Kanketsu-hen_-_Ano_Sora_ni_Kaeru_Mirai_de_(Special)",
    "Buta_no_Gotaku": "Buta_no_Gotoki_Sanzoku_ni_Torawarete_Shojo_wo_Ubawareru_Kyonyuu_Himekishi___Onna_Senshi_(TV)",

    "Cheat_Drugstore": "Cheat_Kusushi_no_Slow_Life:_Isekai_ni_Tsukurou_Drugstore_(TV)",
    "Chiba_pedal_Anzen": "Chiba_Pedal:_Yowamushi_Pedal_to_Manabu_Jitensha_Koutsuu_Anzen_(ONA)",
    "Chiisana_Ahiru": "Chiisana_Ahiru_no_Ooki_na_Ai_no_Monogatari:_Ahiru_no_Kwak_(TV)",
    "Chiisana_Monogatari": "Chiisana_Koi_no_Monogatari:_Chichi_to_Sally_Hatsukoi_no_Shiki_(Special)",
    "Choujin_Koukousei": "Choujin_Koukousei_tachi_wa_Isekai_demo_Yoyuu_de_Ikinuku_you_desu!_(TV)",
    "City_hunter_Saeba": "City_Hunter:_Kinkyuu_Namachuukei!__Kyouakuhan_Saeba_Ryou_no_Saigo_(Special)",
    "Corpse_Party_Souls": "Corpse_Party:_Tortured_Souls_-_Bougyakusareta_Tamashii_no_Jukyou_(OVA)" 
}
    
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
        nurl = url.replace("/", "=").replace(":", "ies").replace("(TV)", "TV").replace(".", "xb").replace(",", "dsj").replace("!", "wq").replace("~","gv").replace("(Movie)", "eiv").replace("(OVA)", "OVA").replace("(Specials)", "Specials").replace("(ONA)", "ONA").replace("Kingdom", "gni").replace("(movie)","vom")
        nurl = nurl.replace("(","lx").replace(")","rx")                                                                                                                                                                                                                                                      
        #movie replace
        yurl = nurl.replace("=movie", "=m").replace("Movie_1", "1M").replace("Movie_2", "2M").replace("Movie_3", "3M").replace("Movie_4", "4M").replace("Movie_5", "5M").replace("Movie_6", "6M").replace("Movie_7", "7M").replace("Movie_8", "8M").replace("Movie_9", "9M").replace("Movie 10", "10M").replace("Episode_of", "oef")                                                                                                                                                                                                                                                     
        #season replace                                                                                                                                                                                                                                                        
        iurl = yurl.replace("=episode", "=e").replace("2nd_Season", "2Z").replace("3rd_Season", "3Z").replace("4th_Season", "4Z").replace("5th_Season", "5Z").replace("6th_Season", "6Z").replace("7th_Season", "7Z").replace("8th_Season", "8Z").replace("9th_Season", "9Z")                                                                                                                                                                                                                         

        xurl = "https://t.me/animeddlbot?start="+iurl
        message_text += f"{i+1}. <a href='{xurl}'>{title}</a>\n"
    
    return message_text, end_idx

def create_ep_results_message(results, start_idx=0):
    message_text = "<b>Search Results:</b>\n\n"
    end_idx = min(start_idx + 25, len(results))
    
    for i in range(start_idx, end_idx):
        title, url = results[i]
        url = url.replace("https://www.tokyoinsider.com/anime/", "")
        url = url.replace("https://tokyoinsider.com/anime/", "")
        nurl = url.replace("/", "=").replace(":", "ies").replace("(TV)", "TV").replace(".", "xb").replace(",", "dsj").replace("!", "wq").replace("~","gv").replace("(Movie)", "eiv").replace("(OVA)", "OVA").replace("(Specials)", "Specials").replace("(ONA)", "ONA").replace("Kingdom", "gni").replace("(movie)", "vom")
        nurl=nurl.replace("(","lx").replace(")","rx")
        
        yurl = nurl.replace("=movie", "=m").replace("Movie_1", "1M").replace("Movie_2", "2M").replace("Movie_3", "3M").replace("Movie_4", "4M").replace("Movie_5", "5M").replace("Movie_6", "6M").replace("Movie_7", "7M").replace("Movie_8", "8M").replace("Movie_9", "9M").replace("Movie 10", "10M").replace("Episode_of", "oef")
        iurl = yurl.replace("=episode", "=e").replace("2nd_Season", "2Z").replace("3rd_Season", "3Z").replace("4th_Season", "4Z").replace("5th_Season", "5Z").replace("6th_Season", "6Z").replace("7th_Season", "7Z").replace("8th_Season", "8Z").replace("9th_Season", "9Z")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
                                                                                                                                                                                                                                                                                    

        print("ep nurl: ", iurl)
        
        xurl = "https://t.me/animeddlbot?start="+iurl
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
    user_id = message.from_user.id
    username = message.from_user.username
    uname = f"@{username}"
    if not await present_user(user_id):
        try:
            await add_user(user_id, uname)
        except:
            pass
    if message.text == "/start":
        await message.reply_text(
            "👋 <b>Hello!</b> I'm an anime search bot.\n\n"
            "📌 <b>Available Commands:</b>\n"
            "/start - Show this message\n"
            "/myquota - Check your remaining searches\n\n"
            "<b>Search Limits:</b>\n"
            "- 5 searches/day for unverified users\n"
            "- 10 searches/day for verified users\n\n"
            "Send me an anime name to search!",
            parse_mode=enums.ParseMode.HTML
        )

    elif any(keyword in query for keyword in ["=e", "=ova", "=m", "=special"]):
        query = query.replace("=", "/").replace("ies", ":").replace("TV", "(TV)").replace("xb", ".").replace("dsj", ",").replace("wq", "!").replace("gv","~").replace("lx","(").replace("rx",")").replace("eiv", "(Movie)").replace("OVA", "(OVA)").replace("Specials", "(Specials)").replace("ONA", "(ONA)").replace("gni","Kingdom").replace("vom", "(movie)")
        query = query.replace("/m", "/movie").replace("1M", "Movie_1").replace("2M", "Movie_2").replace("3M", "Movie_3").replace("4M", "Movie_4").replace("5M", "Movie_5").replace("6M", "Movie_6").replace("7M", "Movie_7").replace("8M", "Movie_8").replace("9M", "Movie_9").replace("10M", "Movie 10").replace("oef", "Episode_of")
        query = query.replace("/e", "/episode").replace("2Z", "2nd_Season").replace("3Z", "3rd_Season").replace("4Z", "4th_Season").replace("5Z", "5th_Season").replace("6Z", "6th_Season").replace("7Z", "7th_Season").replace("8Z", "8th_Season").replace("9Z", "9th_Season")

        dl_url = "https://tokyoinsider.com/anime/"+query
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
    elif query.startswith("verify_"):
        # Handle verification callback
        try:
            target_user_id = int(query.split("_")[1])
            if target_user_id == user_id:
                await mark_user_verified(user_id)
                await message.reply_text(
                    "✅ <b>Verification successful!</b>\n\n"
                    "You now have 10 daily searches available.",
                    parse_mode=enums.ParseMode.HTML
                )
            else:
                await message.reply_text("This verification link is not for you.")
        except:
            await message.reply_text("Invalid verification link.")
    else:
        #equery = b64_to_str(query)
      #  print(equery)
        query= query.replace("=", "/").replace("ies", ":").replace("TV", "(TV)").replace("xb", ".").replace("dsj", ",").replace("wq", "!").replace("gv","~").replace("lx","(").replace("rx",")").replace("eiv", "(Movie)").replace("OVA", "(OVA)").replace("Specials", "(Specials)").replace("ONA", "(ONA)").replace("gni","Kingdom").replace("vom", "(movie)")
        query = query.replace("=m", "=movie").replace("1M", "Movie_1").replace("2M", "Movie_2").replace("3M", "Movie_3").replace("4M", "Movie_4").replace("5M", "Movie_5").replace("6M", "Movie_6").replace("7M", "Movie_7").replace("8M", "Movie_8").replace("9M", "Movie_9").replace("10M", "Movie 10").replace("oef", "Episode_of")
        query = query.replace("=e", "=episode").replace("2Z", "2nd Season").replace("3Z", "3rd Season").replace("4Z", "4th Season").replace("5Z", "5th Season").replace("6Z", "6th Season").replace("7Z", "7th Season").replace("8Z", "8th Season").replace("9Z", "9th Season")
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
        

@app.on_message(filters.text & ~filters.command(["start", "myquota", "broadcast", "users"]))
async def search_anime(client: Client, message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    uname = f"@{username}" if username else str(user_id)
    
    if not await present_user(user_id):
        try:
            await add_user(user_id, uname)
        except:
            pass
    
    # Check search limit
    can_search = await check_search_limit(user_id)
    if not can_search:
        user = await get_user_data(user_id)
        verified = user.get('verified', False)
        
        if not verified:
            # Generate a unique verification token
            token = generate_verification_token()
            await add_verification_token(user_id, token)
            
            # Create verification URL with token
            verification_url = f"https://t.me/{client.me.username}?start=verify_{user_id}_{token}"
            
            # Send verification options with shortened links
            await send_verification_options(client, message, verification_url)
        else:
            await message.reply_text(
                "⚠️ <b>You've reached your daily search limit (10 searches)</b>\n\n"
                "Please try again tomorrow.",
                parse_mode=enums.ParseMode.HTML
            )
        return
    query = message.text.strip()
    if not query:
        return await message.reply_text("Please enter a search query.")
    user = await get_user_data(user_id)
    search_count = user.get('search_count', 0) + 1
    await update_user_search_count(user_id, search_count, user.get('last_reset', datetime.now()))
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

@app.on_message(filters.command('users') & filters.private & filters.user(int(1425489930)))
async def get_users(bot, message: Message):
    msg = await app.send_message(chat_id=message.chat.id, text="`Fetching`")
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@app.on_message(filters.private & filters.command('broadcast') & filters.user(int(1425489930)))
async def send_text(bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        repl = message.reply_to_message_id
        user_id = message.from_user.id
        jar = await bot.get_messages(user_id, repl)
        texter = jar.text
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await bot.send_message(chat_id, texter) 
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await bot.send_message(chat_id, texter) 
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()

# Add this with your other command handlers
@app.on_message(filters.command("myquota"))
async def show_quota(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not await present_user(user_id):
        await message.reply_text("You haven't started using the bot yet. Send any message to begin.")
        return
    
    user = await get_user_data(user_id)
    now = datetime.now()
    last_reset = user.get('last_reset', datetime(1970, 1, 1))
    
    # Check if we need to reset the count (24 hours passed)
    if (now - last_reset) > timedelta(hours=24):
        await update_user_search_count(user_id, 0, now)
        user['search_count'] = 0
        user['last_reset'] = now
    
    search_count = user.get('search_count', 0)
    verified = user.get('verified', False)
    max_searches = 15 if verified else 5
    remaining = max(0, max_searches - search_count)
    
    reset_time = last_reset + timedelta(hours=24)
    hours_until_reset = (reset_time - now).seconds // 3600
    
    await message.reply_text(
        f"🔍 <b>Your Search Quota</b>\n\n"
        f"• Searches used today: {search_count}/{max_searches}\n"
        f"• Remaining searches: {remaining}\n"
        f"• Account type: {'✅ Verified' if verified else '❌ Unverified'}\n"
        f"• Quota resets in: {hours_until_reset} hours\n\n"
        f"{'⚠️ Verify to get 10 daily searches' if not verified else ''}",
        parse_mode=enums.ParseMode.HTML
    )
if __name__ == "__main__":
    print("Bot started...")
    app.run()
