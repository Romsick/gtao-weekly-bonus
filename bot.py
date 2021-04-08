import praw
import json
import os
import re
from datetime import datetime, timedelta
from time import sleep
from discord_webhook import DiscordWebhook, DiscordEmbed

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
            return re.sub(cleanup_rgx, "", f"{post.title}\n\n{post.selftext}")


def build_embed(splitted_text, existing_embed=None):
    if not existing_embed:
        embed = DiscordEmbed(title=datetime.now().strftime("%d-%b-%Y weekly bonuses"), description='', color='b942f5')
        embed.set_footer(text="By Romsick")
    else:
        embed = cleanup_embed(existing_embed)


    title = ''
    items = ''
    for line in splitted_text[1:]:
        if line.startswith('**'):
            if title and items:
                embed.add_embed_field(name=f"__{title}__", value=items + "\n\n", inline=False)
                title = ''
                items = ''
            title = line
        if line.startswith(' -'):
            items = items + line + "\n"
        
    embed.add_embed_field(name=f"__{title}__", value=items + "\n\n", inline=False)

    return embed


def cleanup_embed(embed):
    for i in range(0, len(embed.get_embed_fields())):
        embed.del_embed_field(-1)
    return embed



reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, user_agent=user_agent)
webhook = DiscordWebhook(url=webhook_url)
print("First lookup")
POST_TEXT = get_reddit_post_text(reddit)

if POST_TEXT != None:
    POST_TEXT = POST_TEXT.split("\n\n")

    embed = build_embed(POST_TEXT)
    webhook.add_embed(embed)
    print("Posting first message")
    org_msg = webhook.execute()
else:
    org_msg = None

for iteration in range(1,45):
    # Wait 2min for 1.5h
    print("Waiting for next iteration...")
    sleep(120)
    upd_text = get_reddit_post_text(reddit)
    if upd_text != None:
        upd_text = upd_text.split("\n\n")
    # If the new text is different from the previous text, edit message
    if upd_text != None and POST_TEXT != upd_text:
        webhook.remove_embeds()
        print("Updates in post found... editing message...")
        embed = build_embed(upd_text, embed)
        webhook.add_embed(embed)
        if not org_msg:
            org_msg = webhook.execute()
        else:
            msg = webhook.edit(org_msg)
        POST_TEXT = upd_text

