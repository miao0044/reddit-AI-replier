from __future__ import print_function
import praw
import prawcore
import time
import logging
import random
import requests
from config_en import ACCOUNTS, TARGET_USERS
import os
from openai import OpenAI

# config
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# lord prompt.txt file
def read_prompt_file():
    try:
        with open('prompt_en.txt', 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error("prompt_en.txt file not found.")
        return None

# send request to Grok3 API
def get_grok3_reply(comment_body, prompt):
    os.environ['GROK_API_KEY'] = "grok api"
    client = OpenAI(
        api_key=os.getenv("GROK_API_KEY"),
        base_url="https://api.x.ai/v1"
    )
    X = random.randint(20, 50)
    instruction = f"Generate a response of {X} English words based on the comment."
    messages = [
        {"role": "system", "content": instruction},
        {"role": "system", "content": prompt},
        {"role": "user", "content": comment_body}
    ]
    try:
        response = client.chat.completions.create(
            model="grok-3-mini-beta",
            messages=messages
        )
        return response.choices[0].message.content
    except requests.exceptions.RequestException as e:
        logger.error(f"Grok3 API request failed: {e}")
        return None

# login Reddit account
def bot_login(accounts):
    reddit_instances = []
    for account in accounts:
        try:
            reddit = praw.Reddit(
                client_id=account['client_id'],
                client_secret=account['client_secret'],
                username=account['username'],
                password=account['password'],
                user_agent=account['user_agent']
            )
            reddit_instances.append(reddit)
            logger.info(f"Logged in as {reddit.user.me()}")
        except Exception as e:
            logger.error(f"Failed to log in with account {account['username']}: {e}")
    return reddit_instances

# get newest 3 comments
def get_new_comments(reddit_instance, target_user):
    try:
        redditor = reddit_instance.redditor(target_user)
        latest_comments = list(redditor.comments.new(limit=3))
        return latest_comments
    except Exception as e:
        logger.error(f"Error fetching comments for {target_user}: {e}")
        return []

# reply to comment
def reply_to_comments(reddit_instances, comments):
    prompt = read_prompt_file()
    if prompt is None:
        return

    for comment in comments:
        try:
            comment.refresh()
            replied_usernames = [reply.author.name for reply in comment.replies if reply.author]
        except Exception as e:
            logger.error(f"Error fetching replies for comment {comment.id}: {e}")
            replied_usernames = []

        reply_message = get_grok3_reply(comment.body, prompt)
        if reply_message:
            for reddit_instance in reddit_instances:
                bot_username = reddit_instance.user.me().name
                if bot_username not in replied_usernames:
                    try:
                        comment.reply(reply_message)
                        logger.info(f"Replied to comment {comment.id} using account {bot_username}")
                        sleep_duration = random.randint(20, 70)
                        time.sleep(sleep_duration)
                    except prawcore.exceptions.Forbidden as forbidden_error:
                        logger.warning(f"Permission error for comment {comment.id} with account {bot_username}: {forbidden_error}")
                    except Exception as error:
                        logger.exception(f"Error replying to comment {comment.id} with account {bot_username}: {error}")
                else:
                    logger.info(f"Account {bot_username} has already replied to comment {comment.id}")

# run bot
def run_bot(reddit_instances, target_users):
    for user in target_users:
        try:
            latest_comments = get_new_comments(reddit_instances[0], user)
            logger.info(f"Found {len(latest_comments)} latest comments from {user}")
            reply_to_comments(reddit_instances, latest_comments)
        except Exception as e:
            logger.error(f"Error processing user {user}: {e}")

# main
if __name__ == "__main__":
    reddit_instances = bot_login(ACCOUNTS)
    try:
        run_bot(reddit_instances, TARGET_USERS)
    except Exception as e:
        logger.exception(f"An error occurred: {e}")
    except KeyboardInterrupt:
        logger.info("Bot terminated by user.")