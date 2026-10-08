import os
import re
import random
import string
import requests
from bs4 import BeautifulSoup as bs
from flask import Flask, request, jsonify

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

# ==================== PROXY CONFIGURATION ====================
PROXY_HOST = "proxy.h143.xyz"
PROXY_PORT = "8080"
PROXY_USER_BASE = "9d8a5e623266c5efdebde4aa0be2480b"  # আসল ইউজার আইডি
PROXY_PASS = "1740b522c9c736bd"

def generate_dynamic_proxy():
    """প্রতি রিকোয়েস্টে ইউজারনেমে র‍্যান্ডম সেশন আইডি যোগ করে নতুন আইপি তৈরি করার ফাংশন"""
    random_session = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    # আপনি চাইলে এখানে -country-US বা র‍্যান্ডম সেশন আইডি দিয়ে নতুন আইপি ট্রিগার করতে পারেন
    dynamic_user = f"{PROXY_USER_BASE}-session-{random_session}-country-US"
    proxy_url = f"http://{dynamic_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    return {
        "http": proxy_url,
        "https": proxy_url
    }
# =============================================================

def get_cookies_list():
    if not os.path.exists("cookies.txt"):
        return []
    with open("cookies.txt", "r", encoding="utf-8") as f:
        cookies = [line.strip() for line in f.readlines() if line.strip()]
    return cookies

def parse_cookie_string(cookie_str):
    cookie_dict = {}
    for item in cookie_str.split(";"):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            cookie_dict[key] = value
    return cookie_dict

def extract_target_id(target_url):
    if "id=" in target_url:
        match = re.search(r"id=(\d+)", target_url)
        if match:
            return match.group(1)
    match = re.search(r"facebook\.com/([^/?#]+)", target_url)
    if match:
        return match.group(1)
    return target_url

def do_follow(target_url, cookie_str):
    session = requests.Session()
    
    # প্রতি রিকোয়েস্টে সম্পূর্ণ নতুন ডায়নামিক আইপি প্রক্সি সেসন সেট হবে
    current_proxy = generate_dynamic_proxy()
    session.proxies.update(current_proxy)
    
    cookie_dict = parse_cookie_string(cookie_str)
    
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://mbasic.facebook.com/",
        "Origin": "https://mbasic.facebook.com"
    }
    
    target_id = extract_target_id(target_url)
    
    try:
        profile_url = f"https://mbasic.facebook.com/{target_id}"
        res = session.get(profile_url, headers=headers, cookies=cookie_dict, timeout=15)
        soup = bs(res.text, "html.parser")
        
        fb_dtsg_input = soup.find("input", {"name": "fb_dtsg"})
        jazoest_input = soup.find("input", {"name": "jazoest"})
        
        fb_dtsg = fb_dtsg_input.get("value") if fb_dtsg_input else ""
        jazoest = jazoest_input.get("value") if jazoest_input else ""
        
        follow_href = None
        for a in soup.find_all("a", href=True):
            if "subscribe.php" in a["href"] or "flite=subscribe" in a["href"] or "/follow/" in a["href"]:
                follow_href = a["href"]
                break
                
        if follow_href:
            if not follow_href.startswith("http"):
                follow_href = "https://mbasic.facebook.com" + follow_href
            resp = session.get(follow_href, headers=headers, cookies=cookie_dict, timeout=15)
            if resp.status_code == 200:
                return True
                
        if fb_dtsg:
            follow_payload = {
                "fb_dtsg": fb_dtsg,
                "jazoest": jazoest,
                "location": "11"
            }
            post_url = f"https://mbasic.facebook.com/a/subscribe.php?id={target_id}"
            resp = session.post(post_url, data=follow_payload, headers=headers, cookies=cookie_dict, timeout=15)
            if resp.status_code == 200:
                return True
                
        return False
    except Exception as e:
        print(f"Proxy Connection Error: {e}")
        return False

@app.route("/", methods=["GET"])
def home():
    total_cookies = len(get_cookies_list())
    return jsonify({
        "status": "online",
        "total_loaded_cookies": total_cookies,
        "proxy_rotation": "dynamic_session_enabled"
    })

@app.route("/api/follow", methods=["POST"])
def execute_follow():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"status": "error", "message": "Target 'url' is required"}), 400
        
    target_url = data.get("url")
    count = int(data.get("count", 1))
    
    cookies = get_cookies_list()
    if not cookies:
        return jsonify({"status": "error", "message": "No cookies found in cookies.txt"}), 500
        
    selected_cookies = random.sample(cookies, min(count, len(cookies)))
    success_count = 0
    
    for cookie in selected_cookies:
        if do_follow(target_url, cookie):
            success_count += 1
            
    return jsonify({
        "status": "success",
        "target": target_url,
        "requested_count": count,
        "successful_follows": success_count
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
