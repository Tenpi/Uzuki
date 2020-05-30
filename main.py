import os
import re
import asyncio
import praw
from saucenao_api import SauceNao
from dotenv import load_dotenv
load_dotenv()

client_id = os.getenv("REDDIT_CLIENT_ID")
client_secret = os.getenv("REDDIT_CLIENT_SECRET")
refresh_token = os.getenv("REDDIT_REFRESH_TOKEN")
saucenao_key = os.getenv("SAUCENAO_API_KEY")
user_agent = "Uzuki Bot v1.0 by u/imtenpi"

reddit = praw.Reddit(client_id=client_id, client_secret=client_secret, refresh_token=refresh_token, user_agent=user_agent)

def get_source(link):
    """Gets an image source from the Saucenao API."""
    sauce = SauceNao(api_key=saucenao_key)
    results = sauce.from_url(link)
    url = results[0].url 
    if "pixiv" in url:
        match = re.search(r"\d+", url)
        if match:
            url = f"https://www.pixiv.net/en/artworks/{match.group()}"
    return f"Title: {results[0].title} Artist: {results[0].author} Similarity: {results[0].similarity}\n\nSource: {url}" if len(results) else "Sorry, could not find the source of this drawing!"

def duplicate_source(submission, uzuki=False):
    """Checks if a comment already has a source."""
    if submission.is_self:
        return True
    submission.comments.replace_more(limit=0)
    submission.comment_sort = "old"
    comments = submission.comments.list()
    for comment in comments:
        match = re.search(r"https?://", comment.body, re.IGNORECASE)
        if uzuki and match and comment.author:
            if comment.author.name == "uzukibot":
                return True
        elif not uzuki and match:
            return True
    return False

async def reply(submission, mention=False):
    """Replies on a submission with the source."""
    try:
        source = get_source(submission.url)
    except:
        await asyncio.sleep(30)
        source = get_source(submission.url)
    if mention:
        mention.reply(source)
    else:
        submission.reply(source)
    return

async def automatic_reply():
    """Automatically replies with the source in my subreddits."""
    while True:
        subreddit = reddit.subreddit("AnimeGirlsInLeggings+KawaiiAnimeGirls+WeebsHideout")
        for submission in subreddit.new(limit=25):
            if not duplicate_source(submission):
                await reply(submission)
        await asyncio.sleep(60)

async def mention_reply():
    """Replies with the post source when mentioned."""
    while True:
        for mention in reddit.inbox.mentions(limit=25):
            submission = mention.submission
            if not duplicate_source(submission, True):
                await reply(submission, mention)
        await asyncio.sleep(60)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
        mention_reply(),
        automatic_reply()
    ))
    loop.close()