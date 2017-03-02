import praw
import config
import time
import urllib.request
import os
from bs4 import BeautifulSoup
from slugify import slugify

reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent=config.user_agent)
reddit.read_only = True # might not be needed at all.

subreddits = config.subreddits

# was working on this. might just wanna use some module.
def alb_handler(url):
	page = urllib.request.urlopen(url)
	soup = BeautifulSoup(page, "html.parser")
	all_img1 = soup.find_all("div", { "class" : "post-image"})

while True:
	for sub in subreddits:
		for submission in reddit.subreddit(sub).hot(limit=10):
			# print(submission.title + " " + submission.url)

			temp_path = os.path.join(config.path, slugify(submission.title))
			url = submission.url

			if 'reddit.com/r/' in url:
				continue

			if 'imgur.com/a/' in url:
				alb_handler(url)

			if 'imgur' in url and '.jpg' not in url:
				url += ".jpg"

			if '.jpg' in url:
				temp_path += '.jpg'
			try:
				urllib.request.urlretrieve(url, temp_path)
			except Exception as e:
				print("Request failed: " + str(e))
				pass
		time.sleep(1)

	time.sleep(60)

