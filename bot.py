import praw
import json
import os
import re
from datetime import datetime, timedelta
from time import sleep
from discord_webhook import DiscordWebhook

client_id = os.environ.get("REDDIT_CLIENT_ID")
client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
user_agent = os.environ.get("REDDIT_USER_AGENT")

webhook_id = os.environ.get("WEBHOOK_ID")
webhook_secret = os.environ.get("WEBHOOK_SECRET")
webhook_url = f"https://discord.com/api/webhooks/{webhook_id}/{webhook_secret}"

CLEANUP_REGEX_LIST = [
    r"\[Embedded Updates\]\(.*\)",
    r"\(http.*\)",
    r"\[↗\]\(.*\)",
    r"\[",
    r"\]",
    r"\*Update items.*\*"
]

cleanup_rgx = rf"({'|'.join(CLEANUP_REGEX_LIST)})"

def get_reddit_post_text(reddit_client):
    post_title_search = "Weekly GTA Online Bonuses"
    posts = reddit_client.subreddit('gtaonline').search(post_title_search, sort='new', time_filter='week')
    yesterday_timestamp = (datetime.utcnow() - timedelta(days=1)).timestamp()

    for post in posts:
        # If title starts with date and posted in the last 24h
        if re.match(r"^\d{1,2}\/\d{1,2}\/\d{4}.*$", post.title) and post.created_utc > yesterday_timestamp:
            print(f"{post.title} -- {post.author}")
            return re.sub(cleanup_rgx, "", post.selftext)


reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)

POST_TEXT = get_reddit_post_text(reddit)

webhook = DiscordWebhook(url=webhook_url, content=POST_TEXT)
org_msg = webhook.execute()

for iteration in range(1,37):
    # Wait 10min
    sleep(600)
    upd_text = get_reddit_post_text(reddit)
    # If the new text is different from the previous text, edit message
    if POST_TEXT != upd_text:
        print("Updates in post found... editing message...")
        webhook.content = upd_text
        msg = webhook.edit(org_msg)
        POST_TEXT = upd_text
