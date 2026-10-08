import os
import re
import random
import requests
from bs4 import BeautifulSoup as bs
from flask import Flask, request, jsonify

app = Flask(__name__)

# User Agent Definition
USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

def get_cookies_list():
    """cookies.txt ফাইল থেকে সব কুকি রিড করে লিস্ট আকারে রিটার্ন করে"""
    if not os.path.exists("cookies.txt"):
        return []
    with open("cookies.txt", "r", encoding="utf-8") as f:
        cookies = [line.strip() for line in f.readlines() if line.strip()]
    return cookies

def do_follow(target_url, cookie_str):
    """সরাসরি ফেসবুক পেজ/প্রোফাইল ফলো করার ফাংশন"""
    session = requests.Session()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": cookie_str
    }
    try:
        # mbasic ভার্সনে রিকোয়েস্ট পাঠানো
        clean_url = target_url.replace("www.facebook.com", "mbasic.facebook.com").replace("m.facebook.com", "mbasic.facebook.com")
        res = session.get(clean_url, headers=headers, timeout=10)
        soup = bs(res.text, "html.parser")
        
        # ফলো বাটন খুঁজে বের করা (Ikuti / Follow / Subscribe)
        follow_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/subscribe.php" in href or "flite=subscribe" in href or "/follow/" in href:
                follow_link = href
                break
                
        if follow_link:
            if not follow_link.startswith("http"):
                follow_link = "https://mbasic.facebook.com" + follow_link
            session.get(follow_link, headers=headers, timeout=10)
            return True
        return False
    except Exception as e:
        return False

@app.route("/", methods=["GET"])
def home():
    total_cookies = len(get_cookies_list())
    return jsonify({
        "status": "online",
        "message": "Facebook Auto-Follow API Service is Running",
        "total_loaded_cookies": total_cookies
    })

@app.route("/api/follow", methods=["POST"])
def execute_follow():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"status": "error", "message": "Target 'url' is required"}), 400
        
    target_url = data.get("url")
    count = int(data.get("count", 10)) # ডিফল্ট ১০টি ফলো রিকোয়েস্ট পাঠাবে
    
    cookies = get_cookies_list()
    if not cookies:
        return jsonify({"status": "error", "message": "No cookies found in cookies.txt"}), 500
        
    # র‍্যান্ডম বা ক্রমানুসারে কুকি বাছাই
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
