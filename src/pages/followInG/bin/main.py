import os
import requests
import webbrowser
from instagrapi import Client
from dotenv import load_dotenv
from jinja2 import Template
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import time
from datetime import datetime

# Load environment variables
load_dotenv()

USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
PORT = int(os.getenv('PORT', 8095))
SESSION_FILE = "session.json"
TEMP_FOLDER = "temp"

class CustomHandler(SimpleHTTPRequestHandler):
    """Custom handler to serve files from current directory"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=".", **kwargs)
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

def login():
    """Login to Instagram with session persistence and retry logic"""
    cl = Client()
    
    # Add delays to avoid rate limiting
    cl.delay_range = [3, 6]
    
    # Load previous session if exists
    if os.path.exists(SESSION_FILE):
        try:
            cl.load_settings(SESSION_FILE)
            print("📂 Loaded existing session")
        except Exception as e:
            print(f"⚠️ Couldn't load session: {e}")
    
    try:
        print(f"🔐 Logging in as {USERNAME}...")
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(SESSION_FILE)
        print(f"✅ Logged in successfully")
        return cl
    except Exception as e:
        print(f"❌ Login failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure your password in .env is correct")
        print("2. Try logging into Instagram on your browser first")
        print("3. You might need to complete a security challenge")
        print("4. Wait a few minutes if you've been rate limited")
        exit(1)

def get_user_id_with_retry(cl, max_retries=3):
    """Get user ID with retry logic for rate limiting"""
    for attempt in range(max_retries):
        try:
            user_id = cl.user_id_from_username(USERNAME)
            return user_id
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5
                print(f"⚠️ Rate limited, waiting {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed to get user ID: {e}")
                raise
    return None

def get_non_followers(cl):
    """Compare followers and following to find who doesn't follow back"""
    print("📊 Fetching user ID...")
    user_id = get_user_id_with_retry(cl)
    
    print("👥 Fetching followers list... (this may take a minute)")
    time.sleep(2)  # Small delay before request
    followers = cl.user_followers(user_id)
    
    print("👤 Fetching following list... (this may take a minute)")
    time.sleep(2)  # Small delay before request
    following = cl.user_following(user_id)
    
    followers_set = set(followers.keys())
    following_set = set(following.keys())
    
    print(f"📈 Stats: {len(followers_set)} followers, {len(following_set)} following")
    
    not_following_back = []
    for uid in following_set:
        if uid not in followers_set:
            user_info = following[uid]
            # Convert HttpUrl to string if needed
            pic_url = str(user_info.profile_pic_url) if user_info.profile_pic_url else ""
            
            not_following_back.append({
                "username": user_info.username,
                "full_name": user_info.full_name or user_info.username,
                "profile_pic_url": pic_url,
                "pk": uid
            })
    
    return not_following_back

def download_profile_pictures(users):
    """Download profile pictures to temp folder"""
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    
    # Create a session for requests
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    for idx, user in enumerate(users, 1):
        url = user["profile_pic_url"]
        
        # Ensure url is string
        if not isinstance(url, str):
            url = str(url)
        
        # Try to get higher quality image
        if "_s.jpg" in url:
            url = url.replace("_s.jpg", "_n.jpg")
        elif "150x150" in url:
            url = url.replace("150x150", "320x320")
        
        local_path = os.path.join(TEMP_FOLDER, f"{user['username']}.jpg")
        
        # Skip if already downloaded
        if os.path.exists(local_path):
            user["local_pic"] = local_path
            print(f"  📸 Already have: {user['username']} ({idx}/{len(users)})")
            continue
        
        try:
            print(f"  📥 Downloading: {user['username']} ({idx}/{len(users)})")
            r = session.get(url, timeout=10, stream=True)
            if r.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(1024):
                        f.write(chunk)
                user["local_pic"] = local_path
                print(f"  ✅ Downloaded: {user['username']}")
            else:
                print(f"  ⚠️ HTTP {r.status_code} for {user['username']}, using URL")
                user["local_pic"] = url
            time.sleep(0.5)  # Small delay between downloads
        except Exception as e:
            print(f"  ⚠️ Failed to download {user['username']}: {e}")
            user["local_pic"] = url
    
    return users

def generate_html(users):
    """Generate beautiful HTML report"""
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Instagram: Who doesn't follow back - @{{ username }}</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 20px;
                min-height: 100vh;
            }
            
            .container {
                max-width: 800px;
                margin: 0 auto;
            }
            
            .header {
                background: white;
                border-radius: 20px;
                padding: 30px;
                margin-bottom: 20px;
                text-align: center;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                color: #333;
                font-size: 28px;
                margin-bottom: 10px;
            }
            
            .header .stats {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                border-radius: 15px;
                margin-top: 20px;
            }
            
            .stats-number {
                font-size: 36px;
                font-weight: bold;
            }
            
            .refresh-btn {
                background: #0095f6;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                cursor: pointer;
                margin-top: 15px;
                transition: transform 0.2s;
            }
            
            .refresh-btn:hover {
                transform: scale(1.05);
            }
            
            .user-card {
                background: white;
                border-radius: 15px;
                padding: 15px;
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 15px;
                transition: transform 0.2s, box-shadow 0.2s;
                animation: fadeIn 0.5s ease-out;
            }
            
            .user-card:hover {
                transform: translateX(5px);
                box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            }
            
            @keyframes fadeIn {
                from {
                    opacity: 0;
                    transform: translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .profile-pic {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                object-fit: cover;
                border: 3px solid #0095f6;
            }
            
            .user-info {
                flex: 1;
            }
            
            .username {
                font-weight: 600;
                font-size: 16px;
                color: #262626;
            }
            
            .username a {
                color: #262626;
                text-decoration: none;
            }
            
            .username a:hover {
                color: #0095f6;
            }
            
            .fullname {
                color: #8e8e8e;
                font-size: 14px;
                margin-top: 4px;
            }
            
            .view-profile {
                background: #efefef;
                padding: 8px 16px;
                border-radius: 8px;
                text-decoration: none;
                color: #262626;
                font-size: 14px;
                transition: background 0.2s;
            }
            
            .view-profile:hover {
                background: #dbdbdb;
            }
            
            .empty-state {
                background: white;
                border-radius: 20px;
                padding: 60px;
                text-align: center;
                color: #8e8e8e;
            }
            
            .footer {
                text-align: center;
                color: white;
                margin-top: 30px;
                font-size: 14px;
            }
            
            @media (max-width: 600px) {
                .user-card {
                    flex-wrap: wrap;
                }
                
                .view-profile {
                    width: 100%;
                    text-align: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📸 Instagram Follower Checker</h1>
                <p>@{{ username }}</p>
                <div class="stats">
                    <div class="stats-number">{{ users|length }}</div>
                    <div>people don't follow you back</div>
                </div>
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Page</button>
            </div>
            
            {% if users %}
                {% for user in users %}
                <div class="user-card">
                    <img class="profile-pic" src="{{ user.local_pic }}" alt="{{ user.username }}" onerror="this.src='{{ user.profile_pic_url }}'">
                    <div class="user-info">
                        <div class="username">
                            <a href="https://instagram.com/{{ user.username }}" target="_blank">@{{ user.username }}</a>
                        </div>
                        <div class="fullname">{{ user.full_name }}</div>
                    </div>
                    <a href="https://instagram.com/{{ user.username }}" target="_blank" class="view-profile">View Profile →</a>
                </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    🎉 Amazing! Everyone you follow follows you back!
                </div>
            {% endif %}
            
            <div class="footer">
                Generated on {{ date }} • Instagram Follower Checker
            </div>
        </div>
    </body>
    </html>
    """
    
    template = Template(html_template)
    html_content = template.render(
        username=USERNAME,
        users=users,
        date=datetime.now().strftime("%B %d, %Y at %H:%M")
    )
    
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ HTML report generated: report.html")

def start_server():
    """Start HTTP server on specified port"""
    handler = lambda *args, **kwargs: CustomHandler(*args, directory=".", **kwargs)
    httpd = HTTPServer(("", PORT), handler)
    print(f"\n🌐 Server started at http://localhost:{PORT}")
    print(f"📄 View report: http://localhost:{PORT}/report.html")
    print("⏹️  Press Ctrl+C to stop the server\n")
    
    # Open browser automatically
    webbrowser.open(f"http://localhost:{PORT}/report.html")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Shutting down server...")
        httpd.shutdown()

def main():
    print("🚀 Instagram Follower Checker")
    print("=" * 40)
    
    # Check if credentials exist
    if not USERNAME or not PASSWORD:
        print("❌ Missing credentials in .env file!")
        print("Please create .env with:")
        print("INSTAGRAM_USERNAME=your_username")
        print("INSTAGRAM_PASSWORD=your_password")
        print("PORT=8095")
        exit(1)
    
    # Login to Instagram
    cl = login()
    
    # Get non-followers
    not_following = get_non_followers(cl)
    print(f"\n📋 Found {len(not_following)} users not following you back")
    
    if not_following:
        print("\n💾 Downloading profile pictures...")
        users_with_pics = download_profile_pictures(not_following)
    else:
        users_with_pics = []
    
    # Generate HTML report
    generate_html(users_with_pics)
    
    print("\n✨ All done! Starting web server...")
    print(f"🔌 Serving on port {PORT}")
    
    # Start server (this will block until Ctrl+C)
    start_server()

if __name__ == "__main__":
    main()