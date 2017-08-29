
import time
import os
import threading
import urllib.request
import json
import sys

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

filename = 'data.json'

# dumps to json file
def dump(prop, val):
	with open(filename) as f:
		data = json.load(f)
		data[prop] = val
	os.remove(filename)
	with open(filename, 'w') as f:
		json.dump(data, f, indent=4)

# reads from json file
def read(prop):
	with open(filename) as json_file:
		return json.load(json_file)[prop]

subreddits = read("subs")

if not subreddits:
	print("\nYou haven't added any subs yet. Add them by doing \n\n add <sub> \n")

count = read("count")
limit = read("limit")

# save image
def save_img(link, name, sub=''):
	global count
	ext = '.jpg' if '.jpg' in link else '.png'
	#id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
	filename = f"{slugify(name)}_{sub}{ext}"
	path = os.path.join(config.path, filename)

	try:
		urllib.request.urlretrieve(link, path)
	except Exception as e:
		print(f"Request: {link}: failed: {str(e)}")
		return
	
	count += 1

# check if image exists
def img_exists(name, url):
	ext = '.jpg' if '.jpg' in url else '.png'
	if os.path.isfile(f"{config.path}/{name}{ext}"):
		return True

# handles imgur albums
def alb_handler(url, sub):
	 # gets number after 4th '/'
	alb_id = url.split("/")[4]

	# try getting the album images
	try:
		imgs = client.get_album_images(alb_id)
	except Exception as e:
		print(f"album {alb_id} not found")
		return
	
	# if the album exists and there are no problems, save the images with save_img()
	for x in imgs:
		# check if image already exists
		if img_exists(slugify(f"{str(x.datetime)}_{sub}"), x.link):
			continue
		
		save_img(x.link, str(x.datetime), sub)

# removes all images from specific sub 
def removeimages(sub=''):
	for _, _, filenames in os.walk(config.path):
		for f in filenames:
			try:
				if sub is not '':
					if sub in f:
						os.remove(f"{config.path}/{f}")
				else:
					os.remove(f"{config.path}/{f}")
			except:
				print(f"{f} is in use, try a little later.")
				pass


# the main thread for downloading the images
def img_thread(once=False):
	while True:
		for sub in subreddits:
			try:
				for submission in reddit.subreddit(sub).hot(limit=limit):
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
					if img_exists(f"{slugify(submission.title)}_{sub}", url):
						continue

					save_img(url, submission.title, sub)
			except:
				continue

			time.sleep(0.1)
		dump("count", count)
		if once:
			break
		time.sleep(600)

# removes all images and files incase of emergency D:
def suicide():
	removeimages()

# the thread for getting the input commands.
def inp_thread():
	global subreddits
	global limit
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
		
		if inp.startswith("limit"):
			limit = int(inp.split(" ")[1])
			dump("limit", limit)

		if inp == "count":
			print(read("count"))

		if inp == "stats":
			show_stats()
		
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
				print(f"{k} - {v}")

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
