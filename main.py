
import time
import os
import threading
import urllib.request

import config

import praw
from slugify import slugify
from imgurpython import ImgurClient

reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent=config.user_agent)
reddit.read_only = True # might not be needed at all.

client = ImgurClient(config.imgur_client_id, "")

commands = {
	"run": "runs the image downloader once.", 
	"subs": "shows the subreddit where images are downloaded from.",
	"count": "shows the amount of images totally downloaded.",
	"exit": "exits the image downloader script."
}

subreddits = config.subreddits

count = 0 # global var D:

def save_img(link, name, sub=''):
	global count
	ext = '.jpg' if '.jpg' in link else '.png'
	temp_path = os.path.join(config.path, slugify(name) + "_" + sub + ext) # start using .format()

	try:
		urllib.request.urlretrieve(link, temp_path)
	except Exception as e:
		print("Request:" + link + ": failed: " + str(e))
		pass

	count +=1

def alb_handler(url):
	 # gets number after 4th '/'
	alb_id = url.split("/")[4]

	# try getting the album images
	try:
		imgs = client.get_album_images(alb_id)
	except Exception as e:
		print("album not found " + alb_id)
		return
	
	# if the album exists and there are no problems, save the images with save_img()
	for x in imgs:
		# use 'alb' instead of sub (might wanna change this later)
		save_img(x.link, str(x.datetime), 'alb')

# the main thread for downloading the images.
def img_thread(once=False):
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

				save_img(url, submission.title, sub)

			time.sleep(1)
		if once:
			break
		time.sleep(60)

# the thread for getting the input commands.
def inp_thread():
	global subreddits
	while True:
		inp = input("> ")

		if inp.startswith("add"):
			temp_subreddits = inp.split(" ")[1:]
			for sub in temp_subreddits:
				subreddits.append(sub)
			print(subreddits)
		
		if inp == "count":
			print(count)
		
		if inp == "subs":
			print(subreddits)

		if inp == "run":
			img_thread(once=True)

		if inp == "help":
			for k, v in commands.items():
				print("{} - {}".format(k, v))

		if inp == "exit":
			os._exit(1)

		if inp.startswith("album"):
			alb_url = inp.split(" ")[1]
			alb_handler(alb_url)

			
if __name__ == "__main__":
	t1 = threading.Thread(target=img_thread)
	t2 = threading.Thread(target=inp_thread)
	t1.start()
	t2.start()

