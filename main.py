
import time
import os
import threading
import urllib.request
import json

import config

import praw
from slugify import slugify
from imgurpython import ImgurClient

reddit = praw.Reddit(client_id=config.client_id, client_secret=config.client_secret, user_agent=config.user_agent)
reddit.read_only = True # might not be needed at all.

client = ImgurClient(config.imgur_client_id, "")

commands = {
	"run": "runs the image downloader once.",
	"add <sub>": "add sub(s) to the list.",
	"removesub <sub>": "remove sub from the list.",
	"subs": "shows the subreddit where images are downloaded from.",
	"count": "shows the amount of images totally downloaded.",
	"exit": "exits the image downloader script.",
	"album": "download one album",
	"remove <sub>": "remove all images from one specific subreddit",
	"suicide": "removes all images in specified folder."
}

# dumps to json file
def dump(prop, val):
	with open('json.txt') as f:
		data = json.load(f)
		data[prop] = val
	os.remove('json.txt')
	with open('json.txt', 'w') as f:
		json.dump(data, f, indent=4)

# reads from json file
def read(prop):
	with open('json.txt') as json_file:
		return json.load(json_file)[prop]

subreddits = read("subs")

if not subreddits:
	print("\nYou haven't added any subs yet. Add them by doing \n\n add <sub> \n")

count = read("count")

# save image
def save_img(link, name, sub=''):
	global count
	ext = '.jpg' if '.jpg' in link else '.png'
	temp_path = os.path.join(config.path, slugify(name) + "_" + sub + ext) # start using .format()

	try:
		urllib.request.urlretrieve(link, temp_path)
	except Exception as e:
		print("Request:" + link + ": failed: " + str(e))
		return
	
	count += 1

# check if image exists
def img_exists(name, url):
	ext = '.jpg' if '.jpg' in url else '.png'
	if os.path.isfile(config.path + "/" + name + ext):
		return True

# handles imgur albums
def alb_handler(url, sub):
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
		# check if image already exists
		if img_exists(slugify(str(x.datetime)) + "_" + sub, x.link):
			continue
		
		save_img(x.link, str(x.datetime), sub)

# the main thread for downloading the images
def img_thread(once=False):
	while True:
		for sub in subreddits:
			for submission in reddit.subreddit(sub).hot(limit=10):

				url = submission.url

				if 'reddit.com/r/' in url or 'gifv' in url or 'gif' in url:
					continue

				if 'reddituploads' in url and '.jpg' not in url and '.png' not in url:
					url += ".jpg"

				if 'imgur.com/a/' in url or 'imgur.com/gallery/' in url:
					alb_handler(url, sub)
					continue

				if 'imgur' in url and '.jpg' not in url and '.png' not in url:
					url += ".jpg"
				
				# check if image exists
				if img_exists(slugify(submission.title) + "_" + sub, url):
					continue

				save_img(url, submission.title, sub)

			time.sleep(0.1)
		dump("count", count)
		if once:
			break
		time.sleep(600)

# removes all images from specific sub 
def removeimages(sub):
	for _, _, filenames in os.walk(config.path):
		for f in filenames:
			if sub in f:
				try:
					os.remove(config.path + '/' + f)
				except:
					print(f + " is in use, try a little later.")
					pass

# removes all images incase of emergency D:
def suicide():
	for _, _, filenames in os.walk(config.path):
		for f in filenames:
			os.remove(config.path + '/' + f)

# the thread for getting the input commands.
def inp_thread():
	global subreddits
	while True:
		try:
			inp = input("> ")
		except EOFError:
			os._exit(1)


		if inp.startswith("add"):
			temp_subreddits = inp.split(" ")[1:]
			for sub in temp_subreddits:
				subreddits.append(sub)
			dump("subs", subreddits)
			print(subreddits)
			print("Running once...")
			img_thread(once=True)
		
		if inp.startswith("removesub"):
			temp_subreddit = inp.split(" ")[1]
			subreddits.remove(temp_subreddit)
			dump("subs", subreddits)
			print(subreddits)
		
		if inp == "count":
			print(read("count"))
		
		if inp == "subs":
			print(subreddits)

		if inp == "run":
			img_thread(once=True)

		if inp.startswith("album"):
			alb_url = inp.split(" ")[1]
			alb_handler(alb_url)

		if inp.startswith("remove"):
			sub = inp.split(" ")[1]
			removeimages(sub)

		if inp == "help":
			for k, v in commands.items():
				print("{} - {}".format(k, v))

		if inp == "exit":
			os._exit(1)

		if inp == "suicide":
			if input("You sure? (Y/N) ") == "Y":
				suicide()
				print("RIP.")
			else:
				continue


# all the tread calls.		
if __name__ == "__main__":
	t1 = threading.Thread(target=img_thread)
	t2 = threading.Thread(target=inp_thread)
	t1.start()
	t2.start()
