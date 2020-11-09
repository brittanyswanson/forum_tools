from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException 
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
import time

import mysql.connector
import configparser

timeout = 5
logging = True

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-features=NetworkService")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Helper Functions
def check_for_content_restriction(driver):
    try:
        maintitle = driver.find_element(By.XPATH,"//div[@class='maintitle']")
        if maintitle.text == " CONTENT RESTRICTED":
            return True
        else:
            return False
    except NoSuchElementException:
        print("No maintitle div found.")
        exit()

def navigate_to(url, driver):
    driver.get(url)

    #Handle content restriction if applicable
    if check_for_content_restriction(driver) == True:
        # Day
        day_element = driver.find_element(By.NAME,"day")
        Select(day_element).select_by_value("12")
        # Month
        month_element = driver.find_element(By.NAME,"month")
        Select(month_element).select_by_value("11")
        # Year
        year_element = driver.find_element(By.NAME,"year")
        Select(year_element).select_by_value("1955")
        # "I UNDERSTAND AND WISH TO CONTINUE" button
        continue_button = driver.find_element(By.XPATH,"//input[@value='I understand and wish to continue']")
        continue_button.click()
        time.sleep(5)
        
    return driver

def connect_to_DB():
    config = configparser.ConfigParser()
    config.read('env.ini')

    if 'mysql' in config:
        creds = config['mysql']

        mydb = mysql.connector.connect(
            host = creds['host'],
            database = creds['db'],
            user = creds['user'],
            passwd = creds['passwd'],
            auth_plugin = "mysql_native_password")
    

        try:
            if (mydb):
                status = "connection successful"
            else:
                status = "connection failed"

            if status == "connection successful":
                return mydb
        except Exception as e:
            status = "Failure %s" % str(e)
    else:
        print("Failure getting credentials.")

def get_subforums(driver):
    subforum_dict = { }

    elementListByXpath = driver.find_elements_by_xpath("//div[@class='ind000a']/div[@class='ind000b']//a[contains(@href,'?showforum=')]")

    if len(elementListByXpath) == 0:
        print("Fucked up.")
    else:
        for ele in elementListByXpath:
            subforumLink = ele.get_attribute('href')
            subforumText = ele.text
            # populate dictionary with key-value pair
            subforum_dict[subforumText] = subforumLink
    
    return subforum_dict

def check_for_multiple_pages(driver):
    try:
        pagination = driver.find_element(By.XPATH,"//span[@class='pagination']")
        if pagination.text == ' ':
            return False
        else:
            return True
    except NoSuchElementException:
        return False

def get_characters_on_page(driver,subforum):
    species = subforum
    topic_list = []
    page_list = []

    try:
        elements_present = EC.presence_of_all_elements_located((By.XPATH,"//div[@class='top000a']/div[@class='top000b']//a[contains(@href,'?showtopic=')]"))
        WebDriverWait(driver,timeout).until(elements_present)
        elementListByXpath = driver.find_elements(By.XPATH,"//div[@class='top000a']/div[@class='top000b']//a[contains(@href,'?showtopic=')]")

        if len(elementListByXpath) == 0:
            print("Fucked up getting topics.")
        else:
            for ele in elementListByXpath:
                topicLink = ele.get_attribute('href')
                topicText = ele.text
                #topic_links[topicText] = topicLink
                topic_list.clear()
                topic_list = [topicText, topicLink, species]
                page_list.append(topic_list.copy())
        

            return page_list
    
        
    
    except TimeoutException:
        print("Timed out.")

def insert_database(list_of_records):
    print("Connected to database")
    mydb = connect_to_DB()

    # Statements
    truncate_statement = "TRUNCATE TABLE characters;"
    insert_statement = """REPLACE INTO characters (name, url, species) VALUES (%s, %s, %s)"""

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.execute(truncate_statement)
            print("Truncated table.")
            my_cursor.executemany(insert_statement,list_of_records)
            print("Loaded characters.")
            mydb.commit()
            print(my_cursor.rowcount, " records inserted successfully into character table")
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        mydb.rollback()
        print("Failure")
        return False

def get_active_characters():
    # Configuration values for Chromedriver
    config = configparser.ConfigParser()
    config.read('env.ini')

    if 'chrome' in config:
        path = config['chrome']['path']
    
        driver = webdriver.Chrome(executable_path=path,options=chrome_options)
        driver.implicitly_wait(10)
        
        # Go to the Accepted Applications url
        accepted_applications_url = "http://drivingtowarddeath.jcink.net/index.php?showforum=6"
        driver = navigate_to(accepted_applications_url, driver)

        character_list = []

        # subforums dictionary returned
        # key = subforum name
        # value = url
        character_subforums = get_subforums(driver)

        # Navigate to each sub forum
        for k, v in character_subforums.items():
            driver =  navigate_to(v, driver)
        
            # Get characters (topics) from the page & put in master character list
            temp_topic_list = get_characters_on_page(driver,k)
            # Have to include a reference to the copy of the list or it disappears when we clear it
            character_list.extend(temp_topic_list.copy())
            temp_topic_list.clear()
        
            # Additional Page Logic
            if check_for_multiple_pages(driver) == True:
                other_pages = driver.find_elements(By.XPATH,"/html[1]/body[1]/div[1]/div[4]/table[2]/tbody[1]/tr[1]/td[1]/span[1]//a")
                for pages in other_pages:
                    additional_page_links = []
                    if pages.text != '':
                        page_link = pages.get_attribute('href')
                        additional_page_links.append(page_link)
                
                        # Visit each additional page
                        for link in additional_page_links:
                            driver = navigate_to(link, driver)
                            temp_topic_list = get_characters_on_page(driver,k)
                            if temp_topic_list != None:
                                character_list.extend(temp_topic_list.copy())
                                temp_topic_list.clear()
        print("Finished gathering all characters")
    else:
        print("Warning: Configuration file does not contain a value for chrome path")
        character_list = []
    
    return character_list

        

def main():
    print("Starting population_check.py")
    character_list = get_active_characters()

    insert_database(character_list)





if __name__ == "__main__":
    main()