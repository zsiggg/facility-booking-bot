# Uses selenium and chrome web driver to automatically click booking options that user selected in RUNME.py
# Scheduler from RUNME.py runs main() 2 minutes before specified time

from selenium import webdriver
import time
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from datetime import datetime, timedelta
from subprocess import Popen, call
import glob
import os
import dotenv
import sys
import scheduler

def print_error(error):
    print('----------ERROR----------')
    print(error)

# for recording
# def terminate(process):
#    if process.poll() is None:
#     call('taskkill /F /T /PID ' + str(process.pid))
# def set_recording_name(i, date_today):
#     recording_name = f'/Users/zsig/Documents/Facility Booking Bot/{date_today}_output{i}.mkv'
#     if recording_name in glob.glob('/Users/zsig/Documents/Facility Booking Bot/*.mkv'):
#         return set_recording_name(i+1, date_today)
#     else: return recording_name

# get system time from HTML
def get_sys_time(driver):
    return driver.find_element(By.ID, 'system-clock').text

# selects the option from a dropdown list, given the list's id and the option as a string
def select_dropdown(driver, id, text):
    list = Select(WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            driver.find_element(By.ID, id))))
    list.select_by_visible_text(text)

# select the date from the calendar given
def select_date(driver, id, date_target, day_target, venue_target, activity_target):
    # if unable to click the date in calendar, attempt to refresh the calendar by reselecting venue for 20s
    disabled = True
    start_time = datetime.now()
    while disabled is True and datetime.now() <= start_time + timedelta(seconds=15):
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        driver.find_element(By.ID, id))).click()
        # click next until the correct month (for one year)
        for _ in range(12):
            calendar_header = driver.find_element(By.CLASS_NAME, 'ui-datepicker-header')
            calendar_date = calendar_header.find_element(By.CLASS_NAME, 'ui-datepicker-title')
            if calendar_date.text != date_target:
                calendar_header.find_element(By.XPATH, '//a[@data-handler="next"]').click()
            else:
                break

        calendar = driver.find_element(By.CLASS_NAME, 'ui-datepicker-calendar')
        try:
            calendar_selected_day = calendar.find_element(By.CLASS_NAME, 'ui-datepicker-current-day')
        except NoSuchElementException as exception:
            calendar_selected_day = None

        if calendar_selected_day is not None and calendar_selected_day.text == day_target:
            calendar_selected_day.click()
            return
        else:
            for cell in calendar.find_elements(By.CSS_SELECTOR, 'td'):
                if cell.text == day_target and 'ui-state-disabled' in cell.get_attribute('class'):
                    select_dropdown(driver, 'group_activity_filter', 'Select an activity')
                    select_dropdown(driver, 'group_activity_filter', activity_target)
                    select_dropdown(driver, 'group_venue_filter', 'Select a venue')
                    select_dropdown(driver, 'group_venue_filter', venue_target)
                    break
                elif cell.text == day_target and 'ui-state-disabled' not in cell.get_attribute('class'):
                    cell.click()
                    disabled = False
                    break    

    if disabled is True:
        print_error(f'Unable to select the date ({day_target} {date_target}). Did you enter the correct date? Is today the correct day of booking?')
        driver.quit()
        sys.exit()

# selects all the options on 'Book a Facility' page on REBOKS
def booking(driver, date_time_to_book_on, booking_activity_date_diff, from_target_list, to_target_list, filter_1_target, filter_2_target, activity_target, venue_target, subvenue_list_target):
    driver.get('https://reboks.nus.edu.sg/nus_public_web/public/facilities/group_exclusive_booking')

    select_dropdown(driver, 'group_filter_one', filter_1_target)
    select_dropdown(driver, 'group_filter_two', filter_2_target)

    # calculate the actual activity date and day
    date_time_target = datetime.strptime(date_time_to_book_on[0], '%d/%m/%y').date() + booking_activity_date_diff
    date_target = datetime.strftime(date_time_target, '%B %Y')
    day_target = datetime.strftime(date_time_target, '%d').lstrip('0')

    # wait until the system time is the exact time specified before selecting venue
    time_to_book_on_obj = datetime.strptime(date_time_to_book_on[1], '%H%M')
    while datetime.strptime(get_sys_time(driver), '%X') < time_to_book_on_obj:
        time.sleep(0.5)

    continue_search = True
    count = 1
    while continue_search is True and count <= 3:
        select_dropdown(driver, 'group_activity_filter', activity_target)
        select_dropdown(driver, 'group_venue_filter', venue_target)
        select_date(driver,'date_filter_from', date_target, day_target, venue_target, activity_target)
        select_date(driver, 'date_filter_to', date_target, day_target, venue_target, activity_target)
        driver.execute_script('window.scrollTo(0,0)')   # scroll to top for screen recording of table
        driver.find_element(By.ID, 'search').click()
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')   # scroll to bottom for screen recording of table

        try:
            # select 100 records per page
            list = Select(WebDriverWait(driver, 5).until(EC.element_to_be_clickable(
                    driver.find_element(By.ID, 'table_exclusive_length'))).find_element(By.TAG_NAME, 'select'))
            list.select_by_visible_text('100')
            time.sleep(3)

            table = WebDriverWait(driver, 5).until(EC.presence_of_element_located(
                                (By.ID, 'table_exclusive')))
        except TimeoutException as exception:
            print_error('No table appears after selecting search. Unable to select time slots.')
            break
        
        # loop through each row in table and click those for the specified time slots to be booked
        rows = table.find_elements(By.CSS_SELECTOR, 'tr')[1:]
        if 'dataTables_empty' not in rows[0].find_element(By.CSS_SELECTOR, 'td').get_attribute('class'):
            for row in rows:
                cols = row.find_elements(By.CSS_SELECTOR, 'td')
                subvenue_actual = cols[2].text
                from_actual = cols[4].text
                to_actual = cols[5].text
                if from_actual in from_target_list and to_actual in to_target_list:
                    if len(subvenue_list_target) == 0 or subvenue_actual in subvenue_list_target:
                        WebDriverWait(driver, 10).until(EC.element_to_be_clickable(row)).click()
                        continue_search = False
            if continue_search is True: time.sleep(4)
        else:
            time.sleep(4)   # try 2 more times if no data found in table, or none of the specified slots are in the table
        count += 1
    
    if continue_search is True:
        print_error('Specified time slot(s) not found in the table, or table did not have any data. Others might have booked the slot :(')
        driver.quit()
        sys.exit()
        
    # click add to cart and accept on the popup message
    WebDriverWait(driver,10).until(EC.element_to_be_clickable(
        driver.find_element(By.ID, 'add_cart'))).click()
    WebDriverWait(driver,10).until(EC.alert_is_present())
    driver.switch_to.alert.accept()

def main(recurring, date_time_to_book_on, booking_activity_date_diff , filter_1_target, filter_2_target, activity_target, venue_target, subvenue_list_target, from_target_list, to_target_list, purpose_remark):
    try: 
        # # for recording
        # date_today = datetime.now().strftime('%d%m')
        # recording_name = set_recording_name(0, date_today)
        # recording = Popen(['ffmpeg',  '-f', 'avfoundation', '-r', '30', '-s', '1920x1080', '-i', '1', recording_name]) # start recording

        # initialise the driver
        PATH = os.path.dirname(os.path.realpath(__file__)) + '/chromedriver'
        service = Service(PATH)
        options = webdriver.ChromeOptions()
        options.add_argument('--incognito')
        driver = webdriver.Chrome(service=service, options=options)
        driver.implicitly_wait(3)
        driver.maximize_window()

        driver.get('https://reboks.nus.edu.sg/nus_public_web/public/auth/requestAdfs')

        # enter username and password from .env file
        dotenv.load_dotenv()
        driver.find_element(By.ID, 'userNameInput').send_keys(os.getenv('USER_NAME'))
        driver.find_element(By.ID, 'passwordInput').send_keys(os.getenv('PASSWORD'))
        driver.find_element(By.ID, 'passwordInput').send_keys(Keys.RETURN)

        # switch to group representative acount
        driver.get('https://reboks.nus.edu.sg/nus_public_web/public/profile/supplementary')
        driver.find_element(By.CLASS_NAME, 'switchAccountLink').click()

        # try to execute booking() twice, if no success message after adding to cart
        booked = False
        for _ in range(2):
            booking(driver, date_time_to_book_on, booking_activity_date_diff, from_target_list, to_target_list, filter_1_target, filter_2_target, activity_target, venue_target, subvenue_list_target)
            try:
                # check for green success message after adding to cart
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'alert-success')))
                booked = True
                break
            except TimeoutException as exception:
                continue
        
        if recurring: 
            new_date_obj = datetime.strptime(date_time_to_book_on[0], '%d/%m/%y').date() + timedelta(days=7)
            date_time_to_book_on[0] = datetime.strftime(new_date_obj, '%d/%m/%y')
            variables = [recurring, date_time_to_book_on, booking_activity_date_diff , filter_1_target, filter_2_target, activity_target, venue_target, subvenue_list_target, from_target_list, to_target_list, purpose_remark]
            scheduler.main(args=variables)

        # # go to shopping cart, enter remarks and click submit
        # if booked is True:
        #     driver.get('https://reboks.nus.edu.sg/nus_public_web/public/cart')
        #     WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, 'remark'))).send_keys(purpose_remark)
        #     driver.find_element(By.XPATH, '//input[@name="pay"]').click()
        #     driver.find_element(By.CLASS_NAME, 'page-title-block')

    except:
        print('The booking was not made.')
        # terminate(recording) # for recording

    time.sleep(10)
    driver.quit()