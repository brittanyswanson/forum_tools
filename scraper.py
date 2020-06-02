from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException 
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.common import exceptions 
import time
import datetime
from datetime import datetime

import mysql.connector
import pytz
import csv

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

def write_to_log(string_to_print):
    if logging == True:
        print(string_to_print)

def connect_to_DB():
    mydb = mysql.connector.connect(
        host = "localhost",
        database = "driving_toward_death",
        user = "root",
        passwd = "",
        auth_plugin = "mysql_native_password"
    )

    try:
        if (mydb):
            status = "connection successful"
        else:
            status = "connection failed"

        if status == "connection successful":
            return mydb
    except Exception as e:
        status = "Failure %s" % str(e)

def insert_database(list_of_records):
    mydb = connect_to_DB()

    # Insert statement for single insert
    # insert_statement = "INSERT IGNORE INTO chara (name,nickname,age,occupation,gender,orientation,created_timestamp,topic_id,membergroup_id,faceclaim_id,player_id) VALUES (" +


    # Insert statement for multiple inserts
    insert_statement = "INSERT IGNORE INTO chara (name,nickname,age,occupation,gender,orientation,membergroup,faceclaim,player,created_timestamp,jcink_topic_id,active,updated_timestamp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"


    try:
        if mydb is None:
            connect_to_DB()
        else:
            mydb.ping(True)
            my_cursor = mydb.cursor()
            # my_cursor.execute(mySql_insert_query)
            my_cursor.executemany(insert_statement,list_of_records)
            mydb.commit()
            print(my_cursor.rowcount, "Record inserted successfully into chara table")
            mydb.close()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(str(e))
        mydb.rollback()
        print("Failure")
        return False

def get_subforums(driver):
    write_to_log(str(datetime.now()) + "\t\tget subforums: start")
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
    
    write_to_log(str(datetime.now()) + "\t\tget subforums: end")
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



def get_categories(driver):
    list_of_categories = []

    elementListByXpath = driver.find_elements_by_xpath("//div[@class='maintitle']/a")

    for ele in elementListByXpath:
        category_list = []
        categoryLink = ele.get_attribute('href')
        categoryText = ele.text

        category_list.append(categoryText)
        category_list.append(categoryLink)
        list_of_categories.append(category_list)
    
    return list_of_categories

def get_topics(driver):
    topic_links = []

    try:
        elements_present = EC.presence_of_all_elements_located((By.XPATH,"//div[@class='top000a']/div[@class='top000b']//a[contains(@href,'?showtopic=')]"))
        WebDriverWait(driver,timeout).until(elements_present)
        elementListByXpath = driver.find_elements(By.XPATH,"//div[@class='top000a']/div[@class='top000b']//a[contains(@href,'?showtopic=')]")

        if len(elementListByXpath) == 0:
            print("Fucked up getting topics.")
        else:
            for ele in elementListByXpath:
                topicLink = ele.get_attribute('href')
                #print("The link is: " + str(topicLink))
                topic_links.append(topicLink)
        

            return topic_links
    
        
    
    except TimeoutException:
        print("Timed out.")

# Helper Functions
def navigate_to(url, driver):
    driver.get(url)

    return driver

def convert_time_to_military_time(string_time):
    # "09:36 PM" input to 21:36
    hour = int(string_time[:2])
    location_of_separator = string_time.index(':')

    minute = int(string_time[(location_of_separator + 1):(location_of_separator + 3)])
    meridiem = string_time[-2:]

    if meridiem == "AM":
        if hour == 12:
            hour = 0
    elif meridiem == "PM":
        if hour == 12:
            hour = 12
        else:
            hour = 12 + hour
    
    converted_time = str(hour) + ':' + str(minute)
    return converted_time

def month_to_number(string_month):
    # Assumes the month is the abbreviated
    # example: January

    input_month = string_month.lower()

    if input_month == 'jan':
        return '01'
    elif input_month == 'feb':
        return '02'
    elif input_month == 'mar':
        return '03'
    elif input_month == 'apr':
        return '04'
    elif input_month == 'may':
        return '05'
    elif input_month == 'jun':
        return '06'
    elif input_month == 'jul':
        return '07'
    elif input_month == 'aug':
        return '08'
    elif input_month == 'sep':
        return '09'
    elif input_month == 'oct':
        return '10'
    elif input_month == 'nov':
        return '11'
    elif input_month == 'dec':
        return '12'
    else:
        return "ERROR in month_to_number() "


# More generic helper created for use in format_into_datetime function
# Returns a list of all the split parts
####### REDUNDANT.  PLZ DELETE ME
def split_by_delim(in_string,delimiter):
    write_to_log("****In split_by_delim. Input: " + str(in_string) + " " + str(delimiter))
    if in_string != "":
        split_field = in_string.split(delimiter)
        return split_field
    else:
        print("in_string was empty")
        exit()

def separate_fields_from_value(in_string,delimiter):
    #write_to_log("In separate_fields_from_value.")
    if in_string != "":
        split_field = in_string.split(delimiter)
        return str(split_field[1])
    else:
        print("in_string was empty: " + in_string)

def get_post_id(post_url):
    write_to_log("\t\tget_post_id")
    post_parts = post_url.split('findpost&p=')
    post_id = post_parts[1]
    write_to_log("\t\tpost_id: " + post_id)
    return post_id

def get_post_topic(post_url):
    # assumption is that the url comes in something like:
    # "http://drivingtowarddeath.jcink.net/index.php?showtopic=713"
    # post_parts = post_url.split('findpost&p=')
    post_parts = post_url.split('showtopic=')
    
    #post_topic = post_parts[0].split('&showtopic=')
    #final_post_topic = post_topic[1].split('&')
    #return final_post_topic[0]
    #write_to_log("\t\ttopic_id: " + post_parts[1])
    return post_parts[1]

def format_into_datetime(post_date):
    # DATETIME format should be 'YYYY-MM-DD hh:mm:ss'
    # Scraped post date typically comes in as a string in EDT: "MAY 31 2018, 09:36 PM"
    # write_to_log("\t\tformat_into_datetime.")
    timestamp_parts = post_date.split(', ')
    string_date = timestamp_parts[0]
    string_time = timestamp_parts[1]

    # Date parts
    date_parts = string_date.split(' ')
    month_number = int(month_to_number(date_parts[0]))
    year_number = int(date_parts[2])
    day_number = int(date_parts[1])
    

    # Time parts
    military_time = (convert_time_to_military_time(string_time)).split(':')
    hour = int(military_time[0])
    minutes = int(military_time[1])
    
    
    naive = datetime(year_number, month_number, day_number, hour, minutes)

    return naive

def convert_to_utc(start_datetime):
    # start_datetime should be in format: 'YYYY-MM-DD hh:mm:ss'
    forum_timezone = pytz.timezone('US/Eastern')
    local_dt = forum_timezone.localize(start_datetime, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

# Looking at a single post and returns desired value (date, post_topic_ID, post_id)
def get_post_information(post, desired_value):
    # write_to_log("\t\tget_post_information")
    post_deets = post.find_element(By.XPATH,'//div[@class = "post003"]//a')
    post_url = post_deets.get_attribute('href')
    
    post_date = format_into_datetime(post_deets.text)
    # turn post_date into UTC
    final_post_date = convert_to_utc(post_date)
    


    # post_id = get_post_id(post_url)

    # post_topic_ID = get_post_topic(post_url)


    if desired_value == "date":
        return final_post_date
    # elif desired_value == "post_id":
    #     return post_id
    # elif desired_value == "topic_id":
    #     return post_topic_ID

def add_to_chara_dictionary(chara_details, key_to_add, val_int):
    write_to_log("In add_to_chara_dictionary. Input: chara_details list, " + str(key_to_add) + " " + str(val_int))
    if key_to_add not in chara_details.keys():
        chara_details[key_to_add] = val_int
    return chara_details

    write_to_file(list_of_characters)
    write_to_file(list_of_characters)

def write_to_file(list_to_write):
    now = datetime.now()
    file_name = "active_characters_" + now.strftime("%Y%m%d") + ".csv"
    with open(file_name, 'w', newline='', encoding='UTF-8') as myfile:
        writer = csv.writer(myfile,quoting=csv.QUOTE_NONNUMERIC)
        try:
            writer.writerows(list_to_write)
        except UnicodeEncodeError:
            print("Fail")
        

def get_player_name_from_template(driver,xpath_val):
    try:
        element_present = EC.presence_of_element_located((By.XPATH,'//div[5]//div[1]//div[1]//ul[1]//li[1]'))
        WebDriverWait(driver,timeout).until(element_present)
        player = driver.find_element(By.XPATH,'//div[5]//div[1]//div[1]//ul[1]//li[1]')
        player_name = (player.text).split('\n')

        return player_name[1].lower()

    except:
        print("Timed out looking for player info")

def basic_information_from_application_template(character_url):
    # Custom to "hundredeuro" character template by mitzi from SHINE
    write_to_log(str(datetime.now()) + "\t\tbasic_information_from_application_template: start")

    driver = webdriver.Chrome(executable_path = "C:\\Users\\bende\\projects\\drivers\\chrome_83\\chromedriver.exe", options=chrome_options)
    driver = navigate_to(character_url, driver)
    # Put in a significant wait
    time.sleep(7)
    write_to_log(str(datetime.now()) + "\t\tbasic_information_from_application_template: navigated to character URL")

    character_details = []
    
    try:
        # Click on the Basic Info tab
        element_present = EC.presence_of_element_located((By.XPATH,'//label[@title="basics"]'))
        WebDriverWait(driver,timeout).until(element_present)
        driver.find_element(By.XPATH,'//label[@title="basics"]').click()
        time.sleep(7)
        write_to_log(str(datetime.now()) + "\t\tbasic_information_from_application_template: clicked template's basic info tab")

        # Get li tag elements
        # Examples:
        # <li><b>nicknames</b>" Cyn"</li>
        # <li><b>age</b>" 32"</li>
        elementListByXpath = driver.find_elements_by_xpath("//div[@class='post004']//div[2]//div[1]//div[1]//ul[1]//li")

        # li values into a list
        for li in elementListByXpath:
            if li.text == '':
                print("WARNING: Blank details from li.")
            else:
                temp_field_value = separate_fields_from_value(str(li.text),'\n')
                character_details.append(temp_field_value)

        # Player Info
        # click on ooc tab
        driver.find_element(By.XPATH,'//label[@title="ooc"]').click()
        time.sleep(7)
        write_to_log(str(datetime.now()) + "\t\tbasic_information_from_application_template: clicked template's ooc info tab")

        xpath_val = '//div[5]//div[1]//div[1]//ul[1]//li[1]'
        player_name = get_player_name_from_template(driver,xpath_val)
        character_details.append(player_name)

        # Get post creation time
        posts = driver.find_elements(By.ID,'outerpost')
        post_date = get_post_information(posts[1],"date")
        character_details.append(post_date)
    
        # Get jcink topic id
        topic_id = get_post_topic(character_url)
        character_details.append(int(topic_id))

        # Active
        character_details.append(1)

        # Updated_timestamp
        now = datetime.now(pytz.utc)
        character_details.append(now)


        driver.quit()
        write_to_log(str(datetime.now()) + "\t\tbasic_information_from_application_template: end")
        return character_details
        

    except TimeoutException:
        print("Timed out.")
    
def load_active_characters_in_db(active_characters_urls):
    start_time = datetime.now()
    write_to_log("load_active_characters_in_db:")
    write_to_log("\tstarted at " + str(start_time))

    count = 0
    list_of_characters = []
    # For each character URL in the list
    for active_character in active_characters_urls:
        # Get basic character details
        count+=1
        write_to_log("\tCharacter #: " + str(count))
        chara_details = basic_information_from_application_template(active_character)
        
        list_of_characters.append(chara_details)
        
    end_time = datetime.now()
    write_to_log("\tload_active_characters_in_db: ended at: " + str(end_time))
    write_to_log("\tload_active_characters_in_db: writing details to log.")
    write_to_file(list_of_characters)
    write_to_log("\tload_active_characters_in_db: insert into database.")
    insert_database(list_of_characters)

def get_active_characters():
    start_time = datetime.now()
    write_to_log(str(datetime.now()) + "\t\tget_active_characters: start")
    topics_links = []

    driver = webdriver.Chrome(executable_path = "C:\\Users\\bende\\projects\\drivers\\chrome_83\\chromedriver.exe",options=chrome_options)
    driver.implicitly_wait(10)
    accepted_applications_url = "http://drivingtowarddeath.jcink.net/index.php?showforum=6"
    driver = navigate_to(accepted_applications_url, driver)

    # subforums dictionary returned
    # key = subforum name
    # value = url
    write_to_log(str(datetime.now()) + "\t\tget_active_characters: gather the subforums")
    character_subforums = get_subforums(driver)


    write_to_log(str(datetime.now()) + "\t\tget_active_characters: navigate to each subforum")
    # Iterate over character subforums (species)
    for k, v in character_subforums.items():
        write_to_log(str(datetime.now()) + "\t\tget_active_characters: navigate to " + k)
        driver =  navigate_to(v, driver)
        # Content Restricted page

        if check_for_content_restriction(driver) == True:
            write_to_log("\t\tget_active_characters: Content Restricted")
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

        # Multiple pages?
        if check_for_multiple_pages(driver) == True:
            write_to_log(str(datetime.now()) + "\t\tget_active_characters: Multiple pages located ")
            subforum_topics = get_topics(driver)
            #write_to_log("subforum topics: " + str(len(subforum_topics)))
            #write_to_log("Extend topics_links with subforum_topics.  Before: " + str(len(topics_links)))
            topics_links.extend(subforum_topics)
            #write_to_log("After: " + str(len(topics_links)))
            
            # Process other pages
            # other_pages = driver.find_elements(By.XPATH,"//span[@class='pagination']//a[@class='pagination_page']")
            other_pages = driver.find_elements(By.XPATH,"/html[1]/body[1]/div[1]/div[4]/table[2]/tbody[1]/tr[1]/td[1]/span[1]//a")
            for pages in other_pages:
                additional_page_links = []
                if pages.text != '':
                    page_link = pages.get_attribute('href')
                    additional_page_links.append(page_link)
                    # driver =  navigate_to(page_link, driver)
                    # other_links = get_topics(driver)
                    # for link in other_links:
                    #     topics_links.append(link)
            for link in additional_page_links:
                driver =  navigate_to(page_link, driver)
                additional_topics = get_topics(driver)
                if additional_topics != None:
                    #write_to_log("additional topics: " + str(len(additional_topics)))
                    #write_to_log("Extend topics_links with additional_topics.  Before: " + str(len(topics_links)))
                    topics_links.extend(additional_topics)
                    #write_to_log("After: " + str(len(topics_links)))
        else:
            write_to_log("Single page found.")
            #write_to_log("Extend topics_links with subforum_topics.  Before: " + str(len(topics_links)))
            topics_links.extend(get_topics(driver))
            #write_to_log("After: " + str(len(topics_links)))

    #write_to_log("Total: " + str(len(topics_links)))
    driver.quit()

    end_time = datetime.now()
    write_to_log("get_active_characters:")
    write_to_log("\tcompleted at: " + str(end_time))
    duration = end_time - start_time
    write_to_log("\tduration: " + str(duration))
    return topics_links

def main():
    

    # Testing get_post_topic
    #print(get_post_topic("http://drivingtowarddeath.jcink.net/index.php?showtopic=713"))

    # Testing basic_information_from_application_template
    # basic_information_from_application_template("http://drivingtowarddeath.jcink.net/index.php?showtopic=713")

    # Testing load_active_character_in_db
    # active_character_topics_list = ['http://drivingtowarddeath.jcink.net/index.php?showtopic=3935', 'http://drivingtowarddeath.jcink.net/index.php?showtopic=4911' ]
    # load_active_characters_in_db(active_character_topics_list)

    # Testing get_active_characters()
    # active_character_topics_list = get_active_characters()


    # testing datetime function
    # format_into_datetime("MAY 31 2018, 09:36 PM")


    # print(convert_time_to_military_time("09:36 PM"))
    # print(convert_time_to_military_time("12:46 PM"))
    
    # Testing format_into_datetime
    # post_date = "January 31 2018, 09:36 PM"
    # print("String to convert: " + post_date)
    # formatted_date = format_into_datetime(post_date)
    # print("Datetime format: " + str(formatted_date))

    # Testing convert_to_utc
    # print("Convert to UTC")
    # print(convert_to_utc(formatted_date))

    # -- Testing basic_information_from_application_template --
    # character_details = basic_information_from_application_template("http://drivingtowarddeath.jcink.net/index.php?showtopic=713")
    # for val in character_details:
    #      print(val)

    # -- Production Run -- 
    # active_character_topics_list = get_active_characters()
    # load_active_characters_in_db(active_character_topics_list)

    # -- TEST: get_subforums --
    driver = webdriver.Chrome(executable_path = "C:\\Users\\bende\\projects\\drivers\\chrome_83\\chromedriver.exe",options=chrome_options)
    driver.implicitly_wait(10)
    accepted_applications_url = "http://drivingtowarddeath.jcink.net/index.php?showforum=6"
    driver = navigate_to(accepted_applications_url, driver)
    species_subforums = get_subforums(driver)

    print("User input requested.  Which species?")

    
    
    selected = False
    while selected == False:
        count = 0
        # -- PRINT MENU --
        for species in species_subforums:
            count += 1
            print(str(count) + " " + species)
        
        print("0 EXIT")

        user_input = input("Enter number choice: ")
        # -- TODO: Add validation around user_input

        if int(user_input) != 0:
            count = 0
            for species in species_subforums:
                count += 1
                if count == int(user_input):
                    key_associated_with_chosen_species = species
            
            species_urls = species_subforums[key_associated_with_chosen_species]
                



        elif user_input == "4":
            chosen_species = species_subforums["DRYADS"]
            driver =  navigate_to(species_subforums["AETHERS"], driver)
            if check_for_content_restriction(driver) == True:
                print("Deal with restricted content.")
            else:
                if check_for_multiple_pages(driver) == False:
                    write_to_log(str(datetime.now()) + "\t\tget_active_characters: Multiple pages located ")
                    subforum_topics = get_topics(driver)
                    print(subforum_topics)
        
            selected = True

        else:
            print("Not valid.")



    

if __name__=="__main__": 
    main() 