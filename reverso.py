from playwright.sync_api import sync_playwright
from scrapy import Selector as sel

list_urls = ['https://context.reverso.net/translation/english-arabic/acquisition+planning+systems',
 'https://context.reverso.net/translation/english-arabic/government+procurement']

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=50)
    page = browser.new_page()
    #page.goto('https://context.reverso.net/translation/arabic-english/equity-participation')
    login_page = 'https://account.reverso.net/Account/Login?returnUrl=https%3A%2F%2Fcontext.reverso.net%2F&lang=en'
    page.goto(login_page)

    xpath_email = '//div//input[@id="Email"]'
    xpath_pass = '//div//input[@id="Password"]'
    xpath_log_in_btn = '//button[@type="submit"]'

    xpath_display_more = '//button[@id="load-more-examples"]'

    email = input("""
Enter E-Mail:

""")

    password = input("""
Enter Password:

""")

    page.fill(xpath_email, email)
    page.fill(xpath_pass, password)
    page.click(xpath_log_in_btn)

    trans_page = 'https://context.reverso.net/translation/english-arabic/equity+participation'
    page.goto(trans_page)


    page.click(xpath_display_more)

    for i in range(3):
        page.keyboard.press('End')
        page.wait_for_timeout(2000)
        page.keyboard.press('End')