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
