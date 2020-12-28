import praw
import json
import os
from datetime import datetime, timedelta
from discord_webhook import DiscordWebhook

client_id = os.environ.get("REDDIT_CLIENT_ID")
client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
user_agent = os.environ.get("REDDIT_USER_AGENT")

webhook_id = os.environ.get("WEBHOOK_ID")
webhook_secret = os.environ.get("WEBHOOK_SECRET")
webhook_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_secret}"

post_author = "Call_Me_Tsuikyit"
post_title_search = "Weekly GTA Online Bonuses"

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
posts = reddit.subreddit('gtaonline').search(post_title_search, sort='new', time_filter='week')

yesterday_timestamp = (datetime.utcnow() - timedelta(days=1)).timestamp()

for post in posts:
    # If posted by user we want and in the last 24h
    if post.author == post_author and post.created_utc > yesterday_timestamp:
        webhook = DiscordWebhook(url=webhook_url, content=post.selftext)
        webhook.execute()

    