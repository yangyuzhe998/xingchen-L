import requests
import os
import json
from datetime import datetime
from config.settings import settings

class MoltbookClient:
    """
    Moltbook 社交网络客户端
    负责:
    1. 发帖 (Post)
    2. 回复 (Comment)
    3. 获取 Feed 流
    4. 心跳检查 (Heartbeat)
    """
    def __init__(self):
        self.api_key = settings.MOLTBOOK_API_KEY
        self.agent_name = settings.MOLTBOOK_AGENT_NAME
        self.base_url = settings.MOLTBOOK_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if not self.api_key:
            print("[Moltbook] Warning: API Key not configured.")

    def post(self, title, content, submolt="general"):
        """发布新帖子"""
        url = f"{self.base_url}/posts"
        payload = {
            "submolt": submolt,
            "title": title,
            "content": content
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            print(f"[Moltbook] Posted: {title}")
            return response.json()
        except Exception as e:
            print(f"[Moltbook] Post failed: {e}")
            return None

    def get_feed(self, limit=10, sort="new"):
        """获取最新的 Feed 流"""
        url = f"{self.base_url}/posts?limit={limit}&sort={sort}"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json().get("posts", [])
        except Exception as e:
            print(f"[Moltbook] Get feed failed: {e}")
            return []

    def check_heartbeat(self):
        """
        心跳检查：
        1. 检查是否有未读通知 (暂未实现 API)
        2. 获取最新 Feed 看看有没有感兴趣的话题
        """
        print(f"[Moltbook] Heartbeat check at {datetime.now()}...")
        # 简单检查一下最新帖子
        feed = self.get_feed(limit=5)
        if feed:
            print(f"[Moltbook] Found {len(feed)} new posts in feed.")
            for post in feed:
                print(f"  - [{post.get('submolt')}] {post.get('title')} (by {post.get('author', {}).get('name')})")
        else:
            print("[Moltbook] Feed is empty or fetch failed.")
        return feed

# Global instance
moltbook_client = MoltbookClient()
