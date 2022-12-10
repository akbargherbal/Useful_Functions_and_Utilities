from playwright.sync_api import sync_playwright
from scrapy import Selector as sel

list_urls = ['https://context.reverso.net/translation/english-arabic/acquisition+planning+systems',
 'https://context.reverso.net/translation/english-arabic/government+procurement']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=500)
    page = browser.new_page()
    #page.goto('https://context.reverso.net/translation/arabic-english/equity-participation')
    login_page = 'https://www.fiverr.com/psychicbabe'
    page.goto(login_page)
