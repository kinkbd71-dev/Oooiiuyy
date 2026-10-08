import os
import re
import random
import requests
from bs4 import BeautifulSoup as bs
from flask import Flask, request, jsonify

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"

def get_cookies_list():
    if not os.path.exists("cookies.txt"):
        return []
    with open("cookies.txt", "r", encoding="utf-8") as f:
        cookies = [line.strip() for line in f.readlines() if line.strip()]
    return cookies

def do_follow(target_url, cookie_str):
    session = requests.Session()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": cookie_str
    }
    try:
        # mbasic ভার্সনে প্রোফাইল রিড করা
        clean_url = target_url.replace("www.facebook.com", "mbasic.facebook.com").replace("m.facebook.com", "mbasic.facebook.com")
        res = session.get(clean_url, headers=headers, timeout=15)
        soup = bs(res.text, "html.parser")
        
        # ফলো / সাবস্ক্রাইব লিংক খোঁজা
        follow_link = None
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/subscribe.php" in href or "flite=subscribe" in href or "/follow/" in href:
                follow_link = href
                break
                
        if follow_link:
            if not follow_link.startswith("http"):
                follow_link = "https://mbasic.facebook.com" + follow_link
            
            # ফলো পেজে হিট করা
            follow_res = session.get(follow_link, headers=headers, timeout=15)
            
            # যদি সরাসরি ফলো না হয়ে কনফার্মেশন বা টোকেন চায়
            if "fb_dtsg" in follow_res.text:
                follow_soup = bs(follow_res.text, "html.parser")
                fb_dtsg = follow_soup.find("input", {"name": "fb_dtsg"})
                jazoest = follow_soup.find("input", {"name": "jazoest"})
                form = follow_soup.find("form", action=True)
                
                if fb_dtsg and form:
                    post_data = {
                        "fb_dtsg": fb_dtsg.get("value", ""),
                        "jazoest": jazoest.get("value", "") if jazoest else ""
                    }
                    action_url = form["action"]
                    if not action_url.startswith("http"):
                        action_url = "https://mbasic.facebook.com" + action_url
                    session.post(action_url, data=post_data, headers=headers, timeout=15)
            
            return True
        return False
    except Exception as e:
        return False

@app.route("/", methods=["GET"])
def home():
    total_cookies = len(get_cookies_list())
    return jsonify({
        "status": "online",
        "total_loaded_cookies": total_cookies
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
