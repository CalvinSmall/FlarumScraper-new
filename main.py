import requests
import getpass
import json
from datetime import datetime
import os

##  CONFIGS  ##

prettyprint_json_file=False
pages_to_scrap = ["discussions","users","posts"]
snapshot_interval = 300  # Save snapshot every 300 posts

###############

print("Flarum Forum Scrapper V1.2 - By Folfy_Blue")
forumUrl = input("Forum URL: ")

## FUNCTIONS ##

def login():
    payload = {
        'identification': input("Username: "),
        'password': getpass.getpass(),
        'remember': True
    }
    
    session = requests.Session()
    r = session.post("https://"+forumUrl+"/api/token", data=json.dumps(payload), headers = {"Content-Type": "application/vnd.api+json"})

    if r.status_code == 200:
        token = json.loads(r.content)["token"]
        session.cookies.set("flarum_remember",token, domain=forumUrl)
        return session

def scrapPageWithSnapshots(session, page, scrapTime):
    """Scrap page and save snapshots every N posts"""
    print("Scrapping "+page)
    pages = {}
    post_count = 0
    snapshot_count = 0
    
    nextUrl = "https://"+forumUrl+"/api/"+page
    while True:
        print("Getting data from '"+nextUrl+"'..",end="\r")
        current = session.get(nextUrl)
        content = json.loads(current.content)
        links = content.pop("links")
        
        # Process the content
        for key, value in content.items():
            if type(value) == list:
                if not key in pages:
                    pages[key] = []
                pages[key] += value
                
                # Count posts if this is the posts endpoint
                if page == "posts" and key == "data":
                    post_count += len(value)
        
        # Check if we need to save a snapshot
        if page == "posts" and post_count >= (snapshot_count + 1) * snapshot_interval:
            snapshot_count += 1
            print(f"\nSaving snapshot #{snapshot_count} at {post_count} posts...")
            storeSnapshotData(pages, page, scrapTime, snapshot_count)
        
        if "next" in links:
            nextUrl = links["next"]
        else:
            print("\nDone! Got all "+page+" data.")
            # Save final snapshot if we have remaining data
            if page == "posts" and post_count > snapshot_count * snapshot_interval:
                storeSnapshotData(pages, page, scrapTime, snapshot_count + 1, is_final=True)
            return pages

def storeSnapshotData(data, filename, time, snapshot_num, is_final=False):
    """Store snapshot data with special naming"""
    path = forumUrl+'/'+time+"/"
    if not os.path.exists(forumUrl):
        os.mkdir(forumUrl)
    if not os.path.exists(path):
        os.mkdir(path)

    # Create snapshots directory
    snapshots_path = path + "snapshots/"
    if not os.path.exists(snapshots_path):
        os.mkdir(snapshots_path)

    suffix = "final" if is_final else f"snapshot_{snapshot_num:03d}"
    filepath = snapshots_path + filename + "_" + suffix + ".json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=prettyprint_json_file)
    print("Snapshot data wrote to '"+filepath+"'!")

def storeData(data, filename, time):
    """Original storeData function for non-posts data"""
    path = forumUrl+'/'+time+"/"
    if not os.path.exists(forumUrl):
        os.mkdir(forumUrl)
    if not os.path.exists(path):
        os.mkdir(path)

    with open(path+filename+".json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=prettyprint_json_file)
    print("Data wrote to '"+path+filename+"'!")

################

session = login()
while not session:
    print("Failed to log in!")
    session = login()

print("Logged in!")

scrapTime = datetime.now().strftime("%Y-%m-%d %H;%M;%S")

for page in pages_to_scrap:
    print()
    if page == "posts":
        # Use the new snapshot-aware function for posts
        scrapPageWithSnapshots(session, page, scrapTime)
    else:
        # Use original function for other data
        storeData(scrapPage(session, page), page, scrapTime)

print("-== Finished! ==-")import requests
import getpass
import json
from datetime import datetime
import os
import time
import random
from urllib.parse import urlparse

##  CONFIGS  ##

prettyprint_json_file=False
pages_to_scrap = ["discussions","users","posts"]
snapshot_interval = 300  # Save snapshot every 300 posts
request_delay = 1  # Base delay between requests in seconds
max_retries = 5  # Maximum number of retries for failed requests
use_proxy = False  # Set to True to enable proxy support
proxy_list = []  # List of SOCKS5 proxies in format "socks5://user:pass@host:port"

###############

print("Flarum Forum Scrapper V1.2 - By Folfy_Blue")
forumUrl = input("Forum URL: ")

## FUNCTIONS ##

def login():
    payload = {
        'identification': input("Username: "),
        'password': getpass.getpass(),
        'remember': True
    }
    
    session = requests.Session()
    
    # Configure proxy if enabled
    if use_proxy and proxy_list:
        proxy = random.choice(proxy_list)
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
        print(f"Using proxy: {proxy}")
    
    r = session.post("https://"+forumUrl+"/api/token", data=json.dumps(payload), headers = {"Content-Type": "application/vnd.api+json"})

    if r.status_code == 200:
        token = json.loads(r.content)["token"]
        session.cookies.set("flarum_remember",token, domain=forumUrl)
        return session
    else:
        print(f"Login failed with status code: {r.status_code}")
        return None

def make_request_with_retry(session, url, retries=0):
    """Make HTTP request with retry logic and exponential backoff"""
    try:
        # Add random delay to avoid rate limiting patterns
        delay = request_delay + random.uniform(0, 1)
        time.sleep(delay)
        
        response = session.get(url)
        
        # Handle rate limiting (HTTP 429)
        if response.status_code == 429:
            if retries < max_retries:
                # Exponential backoff with jitter
                wait_time = (2 ** retries) + random.uniform(0, 1)
                print(f"Rate limited. Waiting {wait_time:.2f} seconds before retry {retries+1}/{max_retries}")
                time.sleep(wait_time)
                # Rotate proxy if available
                if use_proxy and proxy_list:
                    proxy = random.choice(proxy_list)
                    session.proxies = {
                        'http': proxy,
                        'https': proxy
                    }
                    print(f"Switching to proxy: {proxy}")
                return make_request_with_retry(session, url, retries + 1)
            else:
                print("Max retries exceeded for rate limiting")
                return response
        
        # Handle other HTTP errors
        if response.status_code != 200:
            if retries < max_retries:
                wait_time = (2 ** retries) + random.uniform(0, 1)
                print(f"Request failed with status {response.status_code}. Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                return make_request_with_retry(session, url, retries + 1)
            else:
                print(f"Max retries exceeded. Last status code: {response.status_code}")
                return response
                
        return response
        
    except requests.exceptions.RequestException as e:
        if retries < max_retries:
            wait_time = (2 ** retries) + random.uniform(0, 1)
            print(f"Request exception: {e}. Retrying in {wait_time:.2f} seconds...")
            time.sleep(wait_time)
            return make_request_with_retry(session, url, retries + 1)
        else:
            print(f"Max retries exceeded with exception: {e}")
            raise

def scrapPageWithSnapshots(session, page, scrapTime):
    """Scrap page and save snapshots every N posts"""
    print("Scrapping "+page)
    pages = {}
    post_count = 0
    snapshot_count = 0
    
    nextUrl = "https://"+forumUrl+"/api/"+page
    request_count = 0
    
    while True:
        print(f"Getting data from '{nextUrl}' (Request #{request_count+1})..",end="\r")
        
        # Make request with retry logic
        current = make_request_with_retry(session, nextUrl)
        
        # Check if request was successful
        if current.status_code != 200:
            print(f"\nFailed to fetch data after {max_retries} attempts. Status code: {current.status_code}")
            break
            
        content = json.loads(current.content)
        links = content.pop("links", {})
        
        # Process the content
        for key, value in content.items():
            if type(value) == list:
                if not key in pages:
                    pages[key] = []
                pages[key] += value
                
                # Count posts if this is the posts endpoint
                if page == "posts" and key == "data":
                    post_count += len(value)
                    print(f"\nTotal posts downloaded: {post_count}")
        
        # Check if we need to save a snapshot
        if page == "posts" and post_count >= (snapshot_count + 1) * snapshot_interval:
            snapshot_count += 1
            print(f"\nSaving snapshot #{snapshot_count} at {post_count} posts...")
            storeSnapshotData(pages, page, scrapTime, snapshot_count)
            
            # Clear accumulated posts to save memory (optional optimization)
            # Uncomment the following lines if you want to clear posts after each snapshot
            # pages["data"] = []
            # print("Cleared post data to save memory")
        
        if "next" in links:
            nextUrl = links["next"]
            request_count += 1
        else:
            print("\nDone! Got all "+page+" data.")
            # Save final snapshot if we have remaining data
            if page == "posts" and post_count > snapshot_count * snapshot_interval:
                storeSnapshotData(pages, page, scrapTime, snapshot_count + 1, is_final=True)
            return pages

def storeSnapshotData(data, filename, time, snapshot_num, is_final=False):
    """Store snapshot data with special naming"""
    path = forumUrl+'/'+time+"/"
    if not os.path.exists(forumUrl):
        os.mkdir(forumUrl)
    if not os.path.exists(path):
        os.mkdir(path)

    # Create snapshots directory
    snapshots_path = path + "snapshots/"
    if not os.path.exists(snapshots_path):
        os.mkdir(snapshots_path)

    suffix = "final" if is_final else f"snapshot_{snapshot_num:03d}"
    filepath = snapshots_path + filename + "_" + suffix + ".json"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=prettyprint_json_file)
    print("Snapshot data wrote to '"+filepath+"'!")

def scrapPage(session, page):
    """Original scrapPage function for non-posts data with retry logic"""
    print("Scrapping "+page)
    pages = {}

    nextUrl = "https://"+forumUrl+"/api/"+page
    request_count = 0
    
    while True:
        print(f"Getting data from '{nextUrl}' (Request #{request_count+1})..",end="\r")
        
        # Make request with retry logic
        current = make_request_with_retry(session, nextUrl)
        
        # Check if request was successful
        if current.status_code != 200:
            print(f"\nFailed to fetch data after {max_retries} attempts. Status code: {current.status_code}")
            break
            
        content = json.loads(current.content)
        links = content.pop("links", {})
        
        for key,value in content.items():
            if type(value) == list:
                if not key in pages:
                    pages[key] = []
                pages[key] += value

        if "next" in links:
            nextUrl = links["next"]
            request_count += 1
        else:
            print("\nDone! Got all "+page+" data.")
            return pages

def storeData(data, filename, time):
    """Original storeData function for non-posts data"""
    path = forumUrl+'/'+time+"/"
    if not os.path.exists(forumUrl):
        os.mkdir(forumUrl)
    if not os.path.exists(path):
        os.mkdir(path)

    with open(path+filename+".json", 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=prettyprint_json_file)
    print("Data wrote to '"+path+filename+"'!")

################

# Proxy configuration example - uncomment and configure if needed
# use_proxy = True
# proxy_list = [
#     "socks5://username:password@proxy1.example.com:1080",
#     "socks5://username:password@proxy2.example.com:1080"
# ]

session = login()
while not session:
    print("Failed to log in!")
    session = login()

print("Logged in!")

scrapTime = datetime.now().strftime("%Y-%m-%d %H;%M;%S")

for page in pages_to_scrap:
    print()
    if page == "posts":
        # Use the new snapshot-aware function for posts
        scrapPageWithSnapshots(session, page, scrapTime)
    else:
        # Use original function for other data
        storeData(scrapPage(session, page), page, scrapTime)

print("-== Finished! ==-")import requests
import getpass
import json
from datetime import datetime
import os

##  CONFIGS  ##

prettyprint_json_file=False
pages_to_scrap = ["discussions","users","posts"]

###############

print("Flarum Forum Scrapper V1.2 - By Folfy_Blue")
forumUrl = input("Forum URL: ")

## FUNCTIONS ##

def login():
	payload = {
		'identification': input("Username: "),
		'password': getpass.getpass(),
		'remember': True
	}
	
	session = requests.Session()
	r = session.post("https://"+forumUrl+"/api/token", data=json.dumps(payload), headers = {"Content-Type": "application/vnd.api+json"})

	if r.status_code == 200:
		token = json.loads(r.content)["token"]
		session.cookies.set("flarum_remember",token, domain=forumUrl)
		return session

def scrapPage(session,page):
	print("Scrapping "+page)
	pages = {} #not good for memory usage because I have a lot of it, fuck you

	nextUrl = "https://"+forumUrl+"/api/"+page
	while True:
		print("Getting data from '"+nextUrl+"'..",end="\r")
		current = session.get(nextUrl)
		content = json.loads(current.content)
		links = content.pop("links")
		for key,value in content.items():
			if type(value) == list:
				if not key in pages:
					pages[key] = []
				pages[key] += value

		if "next" in links:
			nextUrl = links["next"]
		else:
			print("\nDone! Got all "+page+" data.")
			return pages

def storeData(data,filename,time):
	path = forumUrl+'/'+time+"/"
	if not os.path.exists(forumUrl):
		os.mkdir(forumUrl)
	if not os.path.exists(path):
		os.mkdir(path)

	with open(path+filename+".json", 'w', encoding='utf-8') as f:
	    json.dump(data, f, ensure_ascii=False, sort_keys=prettyprint_json_file)
	print("Data wrote to '"+path+filename+"'!")

################

session = login()
while not session:
	print("Failed to log in!")
	session = login()

print("Logged in!")

scrapTime = datetime.now().strftime("%Y-%m-%d %H;%M;%S")

for page in pages_to_scrap:
	print()
	storeData(scrapPage(session,page),page,scrapTime)

print("-== Finished! ==-")
