import praw
import config
import time
import urllib.request
import os
from bs4 import BeautifulSoup
from slugify import slugify
from imgurpython import ImgurClient

reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent=config.user_agent)
reddit.read_only = True # might not be needed at all.

client = ImgurClient(config.imgur_client_id, "")

subreddits = config.subreddits

count = 0

def save_img(link, name):
	global count
	# new syntax
	ext = '.jpg' if '.jpg' in link else '.png'
	temp_path = os.path.join(config.path, slugify(name) + ext)

	try:
		urllib.request.urlretrieve(link, temp_path)
	except Exception as e:
		print("Request:" + link + ": failed: " + str(e))
		pass
	
	print(name + ' ' + link)
	count +=1

# was working on this. might just wanna use some module.
def alb_handler(url):
	alb_id = url.split("/")[4]
	imgs = client.get_album_images(alb_id)
	for x in imgs:
		save_img(x.link, str(x.datetime))


while True:
	for sub in subreddits:
		for submission in reddit.subreddit(sub).hot(limit=10):

			url = submission.url

			if 'reddit.com/r/' in url:
				continue

			if 'reddituploads' in url and '.jpg' not in url and '.png' not in url:
				url += ".jpg"

			if 'imgur.com/a/' in url or 'imgur.com/gallery/' in url:
				alb_handler(url)
				continue

			if 'imgur' in url and '.jpg' not in url and '.png' not in url:
				url += ".jpg"

			save_img(url, submission.title)

		time.sleep(1)
	print(count)
	time.sleep(60)

