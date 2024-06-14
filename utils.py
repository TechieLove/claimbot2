import random
import string
import requests

def generate_gift_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_pastebin_entry(gift_code, cookie_data, pastebin_api_key):
    paste_data = {
        'api_dev_key': pastebin_api_key,
        'api_option': 'paste',
        'api_paste_code': cookie_data,
        'api_paste_name': f'Gift Code: {gift_code}',
        'api_paste_expire_date': '10M'
    }
    response = requests.post("https://pastebin.com/api/api_post.php", data=paste_data)
    if response.status_code == 200:
        return response.text
    else:
        return None

def shorten_url(long_url, url_shortener_api_key):
    linkspay_url = f"https://linkpays.in/api?api={url_shortener_api_key}&url={long_url}&format=text"
    response = requests.get(linkspay_url)
    if response.status_code == 200:
        return response.text.strip()
    else:
        return None
