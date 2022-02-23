# Get the relevant input from the user for booking (e.g. filters, time, date)
# Schedule the job with APScheduler at the specified time, storing in a sqlite database

from dropdown_lists import group_filter_one_list, group_filter_two_list, group_venue_list, group_activity_list, group_subvenue_dic
import os

from datetime import datetime, timedelta
import dotenv
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import inflect
import sys
import scheduler

def user_input(allowed_responses):
    while True:
        response = input().lower()
        if response in allowed_responses:
            return response
        else:
            print('Invalid response!')

# checks if chrome driver is present in the same directory, exits the program otherwise
def check_chrome_driver():
    try:
        PATH = os.path.dirname(os.path.realpath(__file__)) + '/chromedriver'
        service = Service(PATH)
        driver = webdriver.Chrome(service=service)
    except:
        print('You have not installed the web driver for Chrome. Follow the instructions in README.txt after downloading from https://chromedriver.chromium.org/downloads')
        print('Start the program after you have installed the web driver.')
        sys.exit()

# stores login information for NUS account in .env file
def set_login_info():
    print(r'Enter your login information (with nusstu\ included).')
    username = input('Username: ')
    password = input('Password: ')
    with open('.env', 'w') as file:
        file.write(f'USER_NAME={username}\n')
        file.write(f'PASSWORD={password}')

# prompts and returns a list [date, time] of strings
def set_date_time_to_book_on():
    while True:
        while True:
            print('Enter the date and the time that the booking should be made. (the date to go into REBOKS at 9am/9pm)')
            date = input('Date (DD/MM/YY): ')
            try:
                date_obj = datetime.strptime(date, '%d/%m/%y').date()
            except:
                print('Invalid format.')
                continue
            if not date_obj >= datetime.now().date():
                print('Date is before today.')
                continue
            break
        while True:
            time = input('Time (24h format, e.g. 0900, 2100): ')
            try:
                datetime_obj = datetime.strptime(date + ' ' + time, '%d/%m/%y %H%M')
            except:
                print('Invalid format.')
                continue
            if datetime_obj <= datetime.now():
                print('Date and time should be later than the current time.')
                break
            return [date, time]

# prompts and returns a timedelta object, representing diff between booking_date and the activity date
def set_target_date_day(booking_date_time):
    while True:
        date = input('Enter date (of the actual activity) in DD/MM/YY format: ')
        try:
            activity_date = datetime.strptime(date, '%d/%m/%y').date()
        except:
            print('Invalid format.')
            continue
        if not activity_date >= datetime.now().date():
            print('Date is before today.')
        else:
            booking_date = datetime.strptime(booking_date_time[0], '%d/%m/%y').date()
            print(activity_date - booking_date)
            return activity_date - booking_date

# prompts and returns a list of 2 lists [from_list, to_list], where each list contains the start and end times (as strings) respectively
def set_target_time():
    from_list = []
    to_list = []
    count = 1
    engine = inflect.engine()
    while True:
        print(f'Enter {engine.ordinal(count)} 1h duration to be booked for the above filters in 24h format (e.g. 1600, 0900): ')
        from_time = input('From: ')
        to_time = input('To: ')
        try:
            from_time_obj = datetime.strptime(from_time, '%H%M')
            to_time_obj = datetime.strptime(to_time, '%H%M')
        except:
            print('Invalid format.')
            continue
        if (to_time_obj - from_time_obj).seconds/60/60 != 1:
            print('Time is not 1 hour apart.')
        else:
            from_list.append(datetime.strftime(from_time_obj, '%I:%M %p').lstrip('0').lower())
            to_list.append(datetime.strftime(to_time_obj, '%I:%M %p').lstrip('0').lower())
            print('Are there any further 1h durations to be added? (Y/N)')
            if user_input(['y','n']) == 'n':
                return [from_list, to_list]
            else: count+= 1

# prompts and returns the list of choices for the dropdown lists in REBOKS (in the order seen in REBOKS, from top left to bottom right)
def set_target_dropdown_lists():
    choices = []
    print('Select the option from the dropdown list that you would select from the booking page on Reboks.')
    time.sleep(1)
    for list in lists: 
        # automatically choose 'Sports' and 'Other Sports Activity' for the first 2 lists without asking
        if len(list) == 1: 
            choices.append(list[0])
            continue
        while True:
            for i in range(len(list)): print(f'{i+1}: {list[i]}')
            choice = user_input([str(i) for i in range(1, len(list) + 1)])
            print(f'You chose {list[int(choice)-1]}. Confirm? (Y/N)', end=' ')
            if user_input(['y','n']) == 'y': 
                choices.append(list[int(choice)-1])
                break
    if choices[3] in group_subvenue_dic:
        subvenue_list = group_subvenue_dic[choices[3]]
        print('Do you have any subvenues to specify? (Y/N)', end=' ') 
        subvenue_choices = []
        if user_input(['y','n']) == 'y':
            while True:
                for i in range(len(subvenue_list)): print(f'{i+1}: {subvenue_list[i]}')
                choice = user_input([str(i) for i in range(1, len(subvenue_list) + 1)])
                if subvenue_list[int(choice)-1] in subvenue_choices:
                    print(f'Already selected {subvenue_list[int(choice)-1]}!')
                    time.sleep(0.5)
                    continue
                print(f'You chose {subvenue_list[int(choice)-1]}. Confirm? (Y/N)', end=' ')
                if user_input(['y','n']) == 'y': 
                    subvenue_choices.append(subvenue_list[int(choice)-1])
                    print('Subvenues selected:')
                    print('\n'.join(subvenue_choices))
                    print('Are there any further subvenues to be added? (Y/N)')
                    if user_input(['y','n']) == 'y':
                        continue
                    else:
                        choices.append(subvenue_choices)
                        break
        else:
            choices.append([])
    else:
        choices.append([])
    return choices
        
    # # manully input subvenue 
    # print('Do you have any subvenue to specify? The bot will book all the courts in the table for the time slots if no subvenue is specified. (e.g. which multi-purpose court, badminton court...) (Y/N)', end=' ')
    # if user_input(['y','n']) == 'y':
    #     count = 1
    #     engine = inflect.engine()
    #     subvenue_list = []
    #     while True:
    #         print('Subvenue needs to be entered exactly as it would appear in REBOKS (capitals, spaces). Copy and paste from REBOKS table if possible.')
    #         subvenue = input(f'Enter {engine.ordinal(count)} subvenue: ').strip()
    #         subvenue_list.append(subvenue)
    #         print('Are there any further subvenues to be added? (Y/N)')
    #         if user_input(['y','n']) == 'n':
    #             choices.append(subvenue_list)
    #             break
    #         else: count+= 1
    # else:
    #     choices.append([])
    # return choices

# prompts and returns a string of the remark to be entered at the shopping cart page
def set_target_remark():
    print('Finally, input the remark to be inserted into the textbox at the shopping cart page.')
    while True:
        remark = input('Remark: ')
        print('Confirm? (Y/N)', end=' ')
        if user_input(['y','n']) == 'y': return remark


# MAIN CODE
lists = [group_filter_one_list, group_filter_two_list, group_activity_list, group_venue_list]

check_chrome_driver()

# check presence of username and password
dotenv.load_dotenv()
if os.getenv('USER_NAME') is None or os.getenv('PASSWORD') is None:
    print('You have yet to set your login information!')
    set_login_info()
print('Welcome! You may use Ctrl+C to exit this if you make a wrong choice somewhere.')
time.sleep(1)

# menu loop
while True:
    print('1. Enter a new one-time booking')
    print('2. Enter a new recurring booking')
    print('3. Delete a booking')
    print('4. Check pending jobs / start waiting to make the booking')
    print('5. Change login info')
    print('6. Exit')
    response = user_input(['1','2', '3', '4', '5'])
    if response == '1' or response == "2":
        variables = []
        if response == "2":
            print('This following booking will occur every week at the same day and time specified.')
            variables.append(True)
            time.sleep(1)
        else:
            variables.append(False)
        date_time_to_book_on = set_date_time_to_book_on()
        variables.append(date_time_to_book_on)
        variables.append(set_target_date_day(date_time_to_book_on))
        variables.extend(set_target_dropdown_lists())
        variables.extend(set_target_time())
        variables.append(set_target_remark())

        scheduler.main(args=variables)
    elif response == '3':
        scheduler.main(delete_booking_bool=True)
    elif response == '4':
        scheduler.main(check_pending_bookings_bool=True)
    elif response == '5':
        set_login_info()
    else:
        sys.exit()