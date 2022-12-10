from playwright.sync_api import sync_playwright
from scrapy import Selector as sel
from math import ceil
import regex as re
from time import sleep
import regex as re
import os
import pandas as pd

from pathlib import Path
channels_dir = './CHANNELS_LINKS/'
Path(channels_dir).mkdir(parents=True, exist_ok=True)
from datetime import datetime
channels_dir = re.sub(r'[\/\.]+', '', channels_dir)
def time_now():
    '''Get Current Time'''
    
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S.%f")
    print("Current Time =", current_time)
    return now

important_documentation = """
If running this python script on a Linux server (GCP cloud for example):
1) Proper installation of playwright as described in documentation.
2) browsers (drivers) either installed globally on machine or locally.
3) If browsers (drivers) installed locally (in the script directory);
3a) then change directory to the python script directory;
3b) The following prefix will have to be put before the script
3b1) Normally we will do the following: python python_script_path
3b2) In this case we will do the following:
     PLAYWRIGHT_BROWSERS_PATH=$HOME/Playwright_Local/pw-browsers/ python playwright_multiple_youtube_channels_scraper_BETA.py 
"""

# df_selected = pd.read_pickle('TEST_SELECTED_JS_YOUTUBE_CHANNEL.pkl')
df_selected = pd.read_pickle('43_SELECTED_JS_YOUTUBE_CHANNEL.pkl')

list_channel_vid_count = list(zip(df_selected.VIDEO_TAB, df_selected.VIDEO_COUNT))


list_channel_vid_count = list_channel_vid_count[3:]

for (ch_id, channel) in enumerate(list_channel_vid_count):
    print(f'Started Scraping Channel: {ch_id+1} of {len(list_channel_vid_count)}')
    list_failed_channel = []
    try:
        ############
        print('Starting...')
        start = time_now()
        ############

        set_links = set()

        youtube_channel_link = channel[0]
        no_videos = channel[1]

        no_videos = int(no_videos)
        no_of_scrolls = int(ceil(no_videos/25))

        print(f'Number of Videos: {no_videos}')
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
                browser = p.chromium.launch(slow_mo=200, args=['--start-maximized'], timeout=45000) # HEADLESS

                page = browser.new_page()
                #page.set_viewport_size({"width": 1920, "height": 1080})
                page.goto(youtube_channel_link, timeout=45000)

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
                with open(f'./{channels_dir}/{channel_name}.txt', encoding='utf-8', mode='+a') as f:
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
        print(f'Finished Scraping Channel: {ch_id+1} of {len(list_channel_vid_count)}')
        print('----------------------------------------')
    except Exception as e:
        print(e)
        print(f'Failed Scraping {channel[0]}')
        list_failed_channel.append(channel)
        with open('failed_channels.txt', encoding='utf-8', mode='+a') as f:
            for url in list_failed_channel:
                f.write(f'{url}\n')
        print('############################################')
