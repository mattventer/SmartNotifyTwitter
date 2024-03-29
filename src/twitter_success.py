import discord
import tweepy
import requests
from datetime import datetime
import logging


logging.basicConfig(filename = 'src/twit_success.log',level=logging.INFO,
                    format = '%(asctime)s %(levelname)-8s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')


# Load API keys
key_file = 'src/keys.txt'

TWITTER_API_KEY = None
TWITTER_API_SECRET_KEY = None
TWITTER_ACCESS_TOKEN = None
TWITTER_ACCESS_TOKEN_SECRET = None
BOT_TOKEN = None
SUCCESS_CHANNEL = None
load_error = -1

try:
	with open(key_file) as f:
		content = f.readlines()
		content = [x.strip() for x in content]
		f.close()
except:
	logging.error("Could not load info from keys.txt. Make sure file is in correct folder.")
	exit()
else :
	if len(content) == 6:
		TWITTER_API_KEY = content[0]
		TWITTER_API_SECRET_KEY = content[1]
		TWITTER_ACCESS_TOKEN = content[2]
		TWITTER_ACCESS_TOKEN_SECRET = content[3]
		BOT_TOKEN = content[4]
		SUCCESS_CHANNEL = content[5]
		logging.info('Loaded keys.')
	else :
		logging.error('Could not load keys. Check formatting.')
		exit()

################################################################################ Initialize clients# Discord
discord_client = discord.Client()

# Twitter
twit_auth = tweepy.OAuthHandler(TWITTER_API_KEY, TWITTER_API_SECRET_KEY)
twit_auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
twit_client = tweepy.API(twit_auth, wait_on_rate_limit = True,
	wait_on_rate_limit_notify = True)
my_twitter = twit_client.me()
my_twitter_screenname = my_twitter.screen_name

# Client has connected to Discord
@discord_client.event
async def on_ready():
	logging.info(f'Logged in as: {discord_client.user}')


def postTweet(twitter_api, msg, image_filename):
	try:
		res = twitter_api.update_with_media(image_filename, msg)# Post tweet
	except:
		logging.error("Tweet failed")
		return -1
	else:
		logging.info("Tweet posted")
		return f'{res.id}'


@discord_client.event
async def on_message(msg):
	now = datetime.now()
	time_stamp = now.strftime("%m/%d/%Y %H:%M:%S")
	foundImage = False
	image_filename = None
	#logging.info(f'Recieved msg in {msg.channel} from {msg.author}')# Ignore messages from this bot
	if msg.author == discord_client.user:
		return
	elif str(msg.channel) == SUCCESS_CHANNEL: #looking for image to tweet
		for attachment in msg.attachments:
			try:
				url = str(attachment.url)
				#logging.info(f'Found image at {url}')
				image_filename = 'src/new_image.jpg'
				r = requests.get(url)
				# Save locally
				with open(image_filename, 'wb') as f:
					f.write(r.content)
					logging.info('Image saved')
					foundImage = True
			except:
				logging.error('Could not save image')
				foundImage = False
		if foundImage == False: # image not directly embedded, look for link
			url = str(msg.content)
			try:
				r = requests.get(url)
			except:
				logging.warning(f'Message is not an image or url from {msg.author.name}')
				return
			else:
				logging.info(f'Found URL: {url}')
				# Save locally
				if r:
					image_filename = 'src/new_image.jpg'
					with open(image_filename, 'wb') as f:
						f.write(r.content)
						logging.info('Image saved')
						foundImage = True
				else:
					logging.error(f'Found a URL at {url} but could not download image')
		if foundImage == True: # found an image, time to tweet
			tweet_body = f'Success from {msg.author.name} in @NotifySmart'
			if image_filename != None:
				tweet_res = postTweet(twit_client, tweet_body, image_filename)
				if tweet_res != -1:
					#logging.info(f'Success post from {msg.author}')
					post_url = f'https://twitter.com/{my_twitter_screenname}/statuses/{tweet_res}'
					success_embed = discord.Embed(title="SmartNotify Success", color=0xf16868)
					success_embed.add_field(name='Success! Check out your post here:', value=post_url)
					success_embed.set_footer(text="By SmartNotify\t\t" + str(time_stamp), icon_url="https://cdn.discordapp.com/attachments/628750460949364757/631225789538500608/unknown.png")
					success_embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/628750460949364757/631226140601876540/New_logo.png")
					await msg.channel.send(embed=success_embed)
					logging.info(f'{msg.author.name} Tweet Confirmation sent in {SUCCESS_CHANNEL} channel')
				else:
					logging.error('Image was found and saved but failed to tweet.')
			else:
				logging.error('Image filename is None')
	else: #Not in success channel, ingore
		return


try:
	discord_client.run(BOT_TOKEN)
except:
	logging.error('Failed to start Discord bot. Check bot token')
	exit()
