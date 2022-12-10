from playwright.sync_api import sync_playwright
from scrapy import Selector as sel
from math import ceil
import regex as re
from time import sleep
import regex as re
import os
import gc

important_documentation = """
If running this python script on a Linux server (GCP cloud for example):
1) Proper installation of playwright as described in documentation.
2) browsers (drivers) either installed globally on machine or locally.
3) If browsers (drivers) installed locally (in the script directory);
3a) then change directory to the python script directory;
3b) The following prefix will have to be put before the script
3b1) Normally we will do the following: python python_script_path
3b2) In this case we will do the following:
        PLAYWRIGHT_BROWSERS_PATH=pw-browsers/ python python_script_path
     >>>>	PLAYWRIGHT_BROWSERS_PATH=pw-browsers/
"""

from datetime import datetime
def time_now():
    '''Get Current Time'''
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    print("Current Time =", current_time)
    return now


############
print('Starting...')
start = time_now()
############



set_links = set()

youtube_channel_link = input("""
Enter a Youtube Channel Link; Videos Tab:
""")

no_videos = input(f"""
Enter number of videos to be scraped:
""")

while no_videos.isnumeric() == False:
    no_videos =  input(f"""
Enter number of videos to be scraped; the number must be an integer!
You Entered: {no_videos}
""")

no_videos = int(no_videos)
no_of_scrolls = int(ceil(no_videos/25))

print(f'Number of scrolls: {no_of_scrolls}')

#xpath_thumbnails = '//ytd-grid-video-renderer//div[@id="dismissible"]'
xpath_thumbnails = '//div[@id="contents"]//div[@id="dismissible"]'
xpath_video_url = './/div[@id="details"]//a//@href'
xpath_channel_name = '//div[@id="channel-header"]//div[@id="container"]//div[@id="text-container"]//text()'


set_vid_thumbs = set()

set_vid_urls = set()
try:
    with sync_playwright() as p:
        # browser = p.webkit.launch(headless=False, slow_mo=5000) #Debugging With GUI.
        browser = p.chromium.launch(slow_mo=200, args=['--start-maximized']) # HEADLESS

        page = browser.new_page()
        #page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(youtube_channel_link)

        page.wait_for_selector(f'xpath={xpath_thumbnails}')
        page_html = page.content()
        list_thumb = sel(text = str(page_html)).xpath(xpath_thumbnails).getall()
        set_vid_thumbs.update(list_thumb)

        channel_name = sel(text=str(page_html)).xpath(xpath_channel_name).getall()
        channel_name = re.sub(r'\s+', '_', ''.join(channel_name).strip().upper())
        print(f'Channel_Name: {channel_name}')
        
        set_done_vid_thumbs = set()

        for i in range(no_of_scrolls):
            page.keyboard.down("End")
            page_html = page.content()
            list_thumb = sel(text = str(page_html)).xpath(xpath_thumbnails).getall()
            set_vid_thumbs.update(list_thumb)
            
            
            
            for  thumb in (set_vid_thumbs - set_done_vid_thumbs):
                list_urls = sel(text = str(thumb)).xpath(xpath_video_url).getall()
                set_vid_urls.update(list_urls)
                
            
            set_done_vid_thumbs =  set(list(set_vid_thumbs))
            sleep(10/3)
            
            if (i+1) % 5 == 0:
                print(f"""
Current Number of Thumbnails: {len(set_vid_thumbs)} @ {i+1} Iteration
-------------------------------------------------
""".strip())

        print(f'Total Number of Links Scraped: {len(set_vid_urls)}')
        with open(f'{channel_name}.txt', encoding='utf-8', mode='+a') as f:
            for url in set_vid_urls:
                f.write(f'{url}\n')
            
except Exception as e:
    print(e)


end = time_now()
duration = end - start
print(f"""
Total Duration: {duration.seconds} seconds
Number of Videos Links Scraped: {len(set_vid_urls)}
""".strip())
