from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
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
import time
import argparse

timeout = 5
logging = True

# Selenium options
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument("--window-size=1920x1080")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-features=NetworkService")
chrome_options.add_argument("--disable-features=VizDisplayCompositor")
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

# Configuration options loaded from env.ini file
config = configparser.ConfigParser()
config.read('env.ini')
main_url = config['forum_urls']['main_url']
creds = config['mysql']
host = creds['host']
database = creds['db']
user = creds['user']
passwd = creds['passwd']
path = config['chrome']['path']
archived_applications_url = config['forum_urls']['archived_characters']
accepted_applications_url = config['forum_urls']['active_characters']

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
        print("Crap! Content restriction!")
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
    mydb = mysql.connector.connect(
            host = host,
            database = database,
            user = user,
            passwd = passwd,
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

def clean_topic_url(url):
    # Find where the 'showtopic' part of the URL starts
    show_topic_position = url.find('showtopic=')

    if show_topic_position != -1:
        topic_id_start = show_topic_position + 10
        topic_id = url[topic_id_start:(topic_id_start+4)]
        clean_url = main_url + 'showtopic=' + topic_id
        return clean_url

    else:
        print("ERROR: Invalid URL.  Does not contain 'showtopic='")
        return 'ERROR'

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

# **************************************************************************
# Input: driver
#
# Return list of lists (topic_name,url)
# **************************************************************************
# def get_characters_on_page(driver,subforum):
def get_page_topics(driver):
    #species = subforum
    topic_list = []
    page_list = []

    try:
        # Return list of topics
        # elementListByXpath = driver.find_elements(By.XPATH,"//div[@class='top000a']/div[@class='top000b']//a[contains(@href,'?showtopic=')]")
        elementListByXpath = driver.find_elements(By.XPATH,"//div[@class='top-title']//a")


        if len(elementListByXpath) == 0:
            print("ERROR: get_page_topics() Fuck.  No topics found.")
            
        else:
            for ele in elementListByXpath:
                topicLink = clean_topic_url(ele.get_attribute('href'))
                topicText = (ele.text).lower()
                topic_list.clear()
                topic_list = [topicText, topicLink]
                page_list.append(topic_list.copy())
        

            return page_list
    except TimeoutException:
        print("ERROR: get_page_topics() Timed out.")

def char_details(url):
    driver = webdriver.Chrome(executable_path=path,options=chrome_options)
    driver = navigate_to(url, driver)
    try:
        div_element = driver.find_element(By.XPATH,"//div[@class='hundredeuro']/div")
        species = div_element.get_attribute("id")
        print("char_details() > got species")

        # Must check the checkbox to view player
        # Player Info
        # click on ooc tab
        driver.find_element(By.XPATH,'//label[@title="ooc"]').click()
        # Should be div class="tab"
        parent_element = driver.find_element(By.XPATH,'//label[@title="ooc"]').parent
        # ooc_ele = parent_element.find_elements_by_tag_name("li")
        ooc_ele = parent_element.find_elements_by_xpath("//div[@class='info']//li")

        player_info = (ooc_ele[9].text).split('\n')
        player_name = player_info[1].lower()
        print("char_details() > got player name")

        info = [species,player_name]


    except Exception as e:
        print(print("char_details() > Error somewhere in try statement.  Still going on")
        info = ["error", "error"]

    return info

def truncate_character_table():
    print("Connected to database")
    mydb = connect_to_DB()

    # Statement
    truncate_statement = "TRUNCATE TABLE characters;"

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.execute(truncate_statement)
            print("Truncated table.")
            mydb.commit()
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        mydb.rollback()
        print("Failure")
        return False

def insert_database(list_of_records):
    print("Connected to database")
    mydb = connect_to_DB()

    # Statements
    insert_statement = """INSERT INTO characters (name, url, species, active, updated) VALUES (%s, %s, %s, %s, now())"""

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
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

def update_with_details(list_of_records):
    # Used in update_character_stats()
    # list_of_records = [species, player_name, character_url]
    print("Connected to database")
    mydb = connect_to_DB()

    # Statements
    update_statement = """UPDATE characters SET species = %s, player_name = %s WHERE url = %s""" 

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.executemany(update_statement,list_of_records)
            print("Updated Characters.")
            mydb.commit()
            print(my_cursor.rowcount, " records updated successfully in character table")
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        mydb.rollback()
        print("Failure")
        return False

def update_character_activity(list_of_records):
    mydb = connect_to_DB()

    # Statements
    update_statement = """UPDATE characters SET active = 'Y', SET updated = now() WHERE url = %s""" 

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.executemany(update_statement,list_of_records)
            print("Updated Characters.")
            mydb.commit()
            print(my_cursor.rowcount, " records updated successfully into character table")
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        mydb.rollback()
        print("Failure")
        return False

def get_all_characters_from_db(active):
    character_url_list = []
    # Statements
    select_statement = """SELECT url FROM characters"""

    # Inactive Characters
    if active == 'N':
        select_statement = """SELECT url FROM characters WHERE active = 'N'"""
    # Active Characters
    elif active == 'Y':
        select_statement = """SELECT url FROM characters WHERE active = 'Y'"""
    # All
    else:
        select_statement = """SELECT url FROM characters"""

    mydb = connect_to_DB()

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.execute(select_statement)
            all_chars = my_cursor.fetchall()
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        mydb.rollback()
        print("Failure")
        return False
    
    for character in all_chars:
        character_url_list.append(character[0])
    return character_url_list

def get_all_characters_by_player(player):
    character_url_list = []
    # Statements
    select_statement = """SELECT url FROM characters WHERE player_name = 'nitalya/nita'"""

    mydb = connect_to_DB()

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.execute(select_statement)
            all_chars = my_cursor.fetchall()
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        print("Failure getting characters for player: " + str(player))
        return False
    
    for character in all_chars:
        character_url_list.append(character[0])
    return character_url_list
def get_all_characters_with_missing_fields():
    character_url_list = []
    # Statements
    select_statement = """SELECT url FROM characters WHERE species = 'error' or player_name = 'error'"""

    mydb = connect_to_DB()

    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            my_cursor.execute(select_statement)
            all_chars = my_cursor.fetchall()
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        print("Failure getting characters with errors")
        return False
    
    for character in all_chars:
        character_url_list.append(character[0])
    return character_url_list

def get_active_characters():
    print("Getting active characters.")
    character_list = []
    if 'chrome' in config:
        driver = webdriver.Chrome(executable_path=path,options=chrome_options)
        driver.implicitly_wait(10)
        
        driver = navigate_to(accepted_applications_url, driver)

        # subforums dictionary returned
        # key = subforum name
        # value = url
        character_subforums = get_subforums(driver)

        # **************************************************************************
        # TODO: Should read the topics on this first page if there are any.
        # **************************************************************************
        # Navigate to each sub forum
        for subforum_name, subforum_url in character_subforums.items():
            print("Getting topics for " + str(subforum_name))
            driver =  navigate_to(subforum_url, driver)
        
            # Get characters (topics) from the page & put in master character list
            temp_topic_list = get_page_topics(driver)
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
                            temp_topic_list = get_page_topics(driver)
                            if temp_topic_list != None:
                                character_list.extend(temp_topic_list.copy())
                                temp_topic_list.clear()
        temporary_list = []
        print("Rebuilding the list for database insert")
        new_active_characters = []
        update_character_to_active = []
        existing_active_urls = get_all_characters_from_db("Y")
        existing_inactive_urls = get_all_characters_from_db("N")
        for character in character_list:
            # Not existing active
            if character[1] not in existing_active_urls:
                # Not existing inactive
                if character[1] not in existing_inactive_urls:
                    temporary_list.clear()
                    temporary_list = [character[0], character[1],'','Y']
                    new_active_characters.append(temporary_list.copy())
                else:
                    temporary_list.clear()
                    temporary_list = [character[0], character[1],'','Y']
                    update_character_to_active.append(temporary_list.copy())
            else:
                print("Existing character: " + character[0])


        # Insert new characters
        if len(new_active_characters) > 0:
            insert_database(new_active_characters)
        else:
            print("No new active characters.")
        # Update existing characters
        if len(update_character_to_active) > 0:
            update_character_activity(update_character_to_active)
        else:
            print("No characters to update activity status.")
    
def get_archived_characters():
    character_list = []
    driver = webdriver.Chrome(executable_path=path,options=chrome_options)
    driver.implicitly_wait(10)
        
    # Go to the Accepted Applications url
    driver = navigate_to(archived_applications_url, driver)

    # Get characters (topics) from the page & put in master character list
    temp_topic_list = get_page_topics(driver)
    # print("Archived Characters")
    # for topic in temp_topic_list:
    #     print(topic)
    # Have to include a reference to the copy of the list or it disappears when we clear it
    character_list.extend(temp_topic_list.copy())
    temp_topic_list.clear()
        
    # Additional Page Logic
    if check_for_multiple_pages(driver) == True:
        page_num = 2
        page_value = 15
        last_page = driver.find_element(By.XPATH,"//a[@class='pagination_last']")
        page_link = last_page.get_attribute('href')
        # get last page number
        pagination_position = page_link.find('st=')
        pagination_position+=3
        if pagination_position!=-1:
            last_page_value = int(page_link[pagination_position:])

        while page_value <= last_page_value:
            #build url
            pagination_link = archived_applications_url + '&prune_day=100&sort_by=Z-A&sort_key=last_post&st=' + str(page_value)
            driver = navigate_to(pagination_link, driver)
            #get page topics
            time.sleep(3)
            temp_topic_list = get_page_topics(driver)
            if temp_topic_list != None:
                character_list.extend(temp_topic_list.copy())
                temp_topic_list.clear()
            else:
                print("Topic list is empty for some reason!")
            
            if page_value == (last_page_value-15):
                # Should be the next to last page
                page_value = last_page_value
            else:
                page_value += 15

            page_num += 1

        temporary_list = []
        print("Rebuilding the list for database insert")
        new_inactive_characters = []
        update_character_to_inactive = []

        existing_active_urls = get_all_characters_from_db("Y")
        existing_inactive_urls = get_all_characters_from_db("N")
        for character in character_list:
            # Not existing inactive
            if character[1] not in existing_inactive_urls:
                # Not existing active
                if character[1] not in existing_active_urls:
                    temporary_list.clear()
                    temporary_list = [character[0], character[1],'','N']
                    new_inactive_characters.append(temporary_list.copy())
                else:
                    temporary_list.clear()
                    temporary_list = [character[0], character[1],'','N']
                    update_character_to_inactive.append(temporary_list.copy())
            else:
                print("Existing character: " + character[0])


        # Insert new characters
        if len(new_inactive_characters) > 0:
            insert_database(new_inactive_characters)
        else:
            print("No new active characters.")
        # Update existing characters
        if len(update_character_to_inactive) > 0:
            update_character_activity(update_character_to_inactive)
        else:
            print("No characters to update activity status.")
        print("Finished gathering all archived characters")

        print("Rebuilding the list for database insert")
        archived_characters = []
        for character in character_list:
            #rebuild list with species & active status
            archived_characters.append((character[0], character[1],'','N'))
    else:
        print("Not multiple pages.")
        
def get_additional_details_about_character(url):
    temp_list = []
    details_to_insert = []
    # Returns species, character_name for each url
    additional_details = char_details(url)

    # unpack these details
    species = additional_details[0]
    player_name = additional_details[1]

    temp_list.clear()
    temp_list = [species, player_name, url]
    details_to_insert.append(temp_list.copy())
    return details_to_insert

def update_character_stats(active_status):
    details_to_insert = []
    additional_details = []
    temp_list = []
    record_count = 0

    print("update_character_stats() > Getting all characters from db")
    character_url_list = get_all_characters_from_db(active_status)
    for character_url in character_url_list:
        if (record_count%10==0 and record_count !=0):
            print("update_character_stats() > Gathered details from " + str(record_count) + " records")
            update_with_details(details_to_insert)
            details_to_insert.clear()
        #CREATE check_if_application_is_blank()
        # Returns species, character_name for each url'
        additional_details = char_details(character_url)

        # unpack these details
        if len(additional_details) < 1:
            print("update_character_stats() > Error getting the species and player name for " + str(character_url))
        else:
            species = additional_details[0]
            player_name = additional_details[1]

            temp_list.clear()
            temp_list = [species, player_name, character_url]
            details_to_insert.append(temp_list.copy())
        record_count+=1
        

    print("update_character_stats() > Update database with details in list.")
    update_with_details(details_to_insert)

def main():
    # Initialize parser
    my_parser = argparse.ArgumentParser()

    # Adding optional argument
    # my_parser.add_argument('-input', action='store', type=str, required=True)
    my_parser.add_argument('-a', '--active', action='store_true', help='execute the active character scripts')
    my_parser.add_argument('-ar', '--archived', action='store_true', help='execute the archived character scripts')
    my_parser.add_argument('-up_stats', '--update_stats', action='store', help='update the stats of the character.  Provide Y for active or N for archived')
    my_parser.add_argument('-err', '--error_rerun', action='store_true', help='re-run characters with player and species fields in error')
    my_parser.add_argument('-up_char', '--update_character', action='store', help='single run to update a character stat.  Provide url')

    # Read arguments from command line
    args = my_parser.parse_args()
    
    # -----------------------------------------------------------
    # Active Characters Run
    # -----------------------------------------------------------
    if args.active:
        print("Getting active characters to insert in db")
        get_active_characters()

    # -----------------------------------------------------------
    # Archived Characters Run
    # -----------------------------------------------------------
    elif args.archived:
        print("Getting archived characters to insert in db")
        get_archived_characters()

    # -----------------------------------------------------------
    # Update character stats - requires input of Y or N
    # -----------------------------------------------------------
    elif args.update_stats:
        print("Update character stats with active characters only? ")
        wants_active = args.update_stats
        if wants_active == 'Y' or wants_active == 'y':
            update_character_stats('Y')

    # -----------------------------------------------------------
    # Re-process the characters with errors in species or player
    # -----------------------------------------------------------
    elif args.error_rerun:
        error_characters = get_all_characters_with_missing_fields()
        for i in error_characters:
            char_details = get_additional_details_about_character(i)
            # char_details = [species, player_name, url]
            update_with_details(char_details)
    # -----------------------------------------------------------
    # Individual URL to update character details
    # -----------------------------------------------------------
    elif args.update_character:
        char_url = args.update_character
        char_details = get_additional_details_about_character(char_url)
        update_with_details(char_details)

    else:
        print('What have you done?')



    # Individual player to update character details
    # -----------------------------------------------------------
    # player = 'nitalya/nita'
    # player_characters = get_all_characters_by_player(player)
    # for i in player_characters:
    #     char_details = get_additional_details_about_character(i)
    #     update_with_details(char_details)
        


if __name__ == "__main__":
    main()