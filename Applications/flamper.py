
import os
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class Flamper:

#---------------------------------------------------------------------------------------------------------
#---Initializations---------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

    #Path to browser driver, can be downloaded at:
    #https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-win64.zip
    #https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-win32.zip
    browser_driver = "C:/Program Files/Mozilla Firefox/geckodriver.exe"

    def __init__(self, reviews_url = 'https://novosibirsk.flamp.ru/firm/novosibirskijj_gosudarstvennyjj_tekhnicheskijj_universitet-141265769349251'):

        #Reviews store variable
        self.reviews = []

        #self.reviews_url = 'https://novosibirsk.flamp.ru/firm/novosibirskijj_gosudarstvennyjj_tekhnicheskijj_universitet-141265769349251'
        self.reviews_url = reviews_url

        #We will use firefox, but you can try something else
        browser_options = webdriver.FirefoxOptions()
        #Headless means 'without visible window'
        browser_options.add_argument('-headless')
        #Initialize web-browser object
        self.browser = webdriver.Firefox(executable_path=Flamper.browser_driver, options=browser_options)

    def __len__(self):
        return len(self.reviews)

    def __getitem__(self, position):
        return self.reviews[position]

    def __repr__(self):
        return (f"Totally {self.__len__()} reviews on "
                f"{self.reviews_url} link")

#---------------------------------------------------------------------------------------------------------
#---Retrievers--------------------------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------

    def _reviews_retriever(self):

        #Retrieve page located on our url
        self.browser.get(self.reviews_url)
        #Looking for a button which, displays more reviews when pressed
        button = self.browser.find_elements_by_xpath("//*[contains(text(), 'Показать ещё отзывы')]")
        #Click it
        button[0].click()

        #Get page content
        page_content = self.browser.page_source
        #Start to parse it
        soup = BeautifulSoup(page_content, features="html.parser")
        #Looking for a total amount of available reviews
        reviews_count_raw = soup.find("meta", {"itemprop": "reviewCount"})
        reviews_count = int(reviews_count_raw.attrs['content'])

        with tqdm(total=reviews_count) as pbar:
            #While there are some reviews which not collected yet
            while (len(self.reviews) < reviews_count):
                #Get page content
                page_content = self.browser.page_source
                #Start to parse it
                soup = BeautifulSoup(page_content, features="html.parser")
                #Find reviews items
                another_reviews_pick = soup.findAll("div", {"class": "t-text t-rich-text ugc-item__text ugc-item__text--full js-ugc-item-text-full"})
                #Check reviews in new batch for no entry in already harvested batch condition
                for review in another_reviews_pick:
                    if review.text not in self.reviews:
                        self.reviews.append(review.text)
                '''
                os.system('cls')
                print(f"Retrieved: {len(self.reviews)} reviews")
                print(self.browser.execute_script("return document.body.scrollHeight"))
                '''
                
                #Scroll page down
                activity = self.browser.find_elements_by_tag_name('html')
                activity[0].send_keys(Keys.END)

                pbar.update(2)
        #Close invisible browser
        self.browser.quit()