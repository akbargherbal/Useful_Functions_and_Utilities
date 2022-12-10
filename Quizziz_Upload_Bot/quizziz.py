from playwright.sync_api import sync_playwright
from scrapy import Selector as sel
from time import sleep
from creds import user_name, password

print(user_name)

# PAGE: LOGIN XPATHS
xpath_user_name = """//div[@class="user-id-field"]//input[@type="text"]""".strip()
xpath_password = """//div[@class="user-pass-field"]//input[@type="password"]""".strip()
xpath_submit_button = """//button[@type="submit"]""".strip()

# PAGE: LOGGED IN XPATHS
xpath_create_button = """//button//span[contains(text(), "Create")]""".strip()


# PAGE: QUIZ INITIALIZATION XPATHS
xpath_quiz_select_bttn = """//span[contains(text(), "Quiz")]""".strip()
xpath_topic_select_bttn = """//button//span[contains(text(), "English")]""".strip()
xpath_name_this_quiz = """(//label[contains(text(), "Name this quiz")])/../div//input""".strip()
xpath_next_bttn = """//span[contains(text(), "Next")]""".strip()
name_this_quiz = "Created_by_Playwright_01"


# PAGE: Choose type of Quiz: Open-Ended.
xpath_open_ended_question = """//div[@class="for-super"]//*[contains(text(), "Open-ended")]""".strip()


# PAGE: Fill Open-Ended Question
xpath_open_ended_q_text = """(//*[contains(@data-placeholder, "Type your question here")])""".strip()
random_text = "Some Random Text....... by Playwright"
xpath_first_q_save =  """//span[contains(text(), "Save")]""".strip()

# PAGE MAIN QUIZ PAGE;
xpath_import_from_spreadsheet = """//*[contains(text(), "Import from spreadsheet")]""".strip()


# UPLOAD PHOTO AND SPREADSHEET;
photo_upload = r"C:\Users\gherb\Jupyter_Notebooks\Quizziz_Upload_Bot\picture.png"
excel_upload = r"C:\Users\gherb\Jupyter_Notebooks\Quizziz_Upload_Bot\quiz_bank.xlsx"

xpath_click_uplaod_image = """//span[contains(text(), "Click here to upload a quiz image")]""".strip()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=1000)
    
    page = browser.new_page()
    login_page = 'https://quizizz.com/login'
    page.goto(login_page)

    page.is_visible(xpath_user_name)
    page.fill(xpath_user_name, user_name)
    page.fill(xpath_password, password)
    page.click(xpath_submit_button)

    page.is_visible(xpath_create_button)
    page.click(xpath_create_button)

    page.fill(xpath_name_this_quiz, name_this_quiz)
    page.click(xpath_quiz_select_bttn)
    page.click(xpath_topic_select_bttn)
    page.click(xpath_next_bttn)

    # Create Placeholder OPEN-ENDED QUIZ:
    page.click(xpath_open_ended_question)

    page.fill(xpath_open_ended_q_text, random_text)
    page.click(xpath_first_q_save)

    page.is_visible("""//span[contains(text(), "1 Questions")]""".strip())

    page.click(xpath_click_uplaod_image)

    page.set_input_files('//input[@type="file"]', photo_upload)
    page.is_hidden('//span[contains(text(), "Change Question Order")]')

    #page.select_option("""//div[contains(text(), "—From—")]""", 'Professional Developmen')
    page.click('//*[contains(text(), "—From—")]')
    page.click('(//div[contains(text(), "Professional Develop")])[1]')

    page.click('((//span[contains(text(), "Cancel")])/..)/../button//span[contains(text(), "Save")]')

    page.click(xpath_import_from_spreadsheet)
    page.set_input_files('//input[@type="file"]', excel_upload)

    page.click('((//span[contains(text(), "Cancel")])/..)/../button//span[contains(text(), "Import")]')

    page.click("""
(//p[contains(text(), "Some Random Text....... by Playwright")])/ancestor::div[4]//button[@aria-label="Delete this question"]
    """.strip())

    page.click("""
//*[contains(text(),  "Are you sure you want to delete this question?")]/ancestor::div[3]//span[contains(text(), "Delete")]
""".strip())

    page.click("""//nav//span[contains(text(), "Save")]""")
    page.click('((//span[contains(text(), "Cancel")])/..)/../button//span[contains(text(), "Save")]')
    
    
    print('SAVED FIRST QUESTION OPEN-ENDED QUIZ')