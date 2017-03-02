import praw
import config

reddit = praw.Reddit(client_id=config.client_id,
                     client_secret=config.client_secret,
                     user_agent=config.user_agent)
reddit.read_only = True
for submission in reddit.subreddit('learnpython').hot(limit=10):
    print(submission.title)