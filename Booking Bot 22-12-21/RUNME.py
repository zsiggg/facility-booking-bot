# Get the relevant input from the user for booking (e.g. filters, time, date)
# Schedule the job with APScheduler at the specified time, storing in a sqlite database

from dropdown_lists import group_filter_one_list, group_filter_two_list, group_venue_list, group_activity_list
import os

from datetime import datetime, timedelta
import dotenv
import time
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import inflect
import sys

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

# prompts and returns a list [date, day], where date is the month + year string, and day is a non-zero padded string
def set_target_date_day():
    while True:
        date = input('Enter date (of the actual activity) in DD/MM/YY format: ')
        try:
            date_obj = datetime.strptime(date, '%d/%m/%y').date()
        except:
            print('Invalid format.')
            continue
        if not date_obj >= datetime.now().date():
            print('Date is before today.')
        else:
            date = datetime.strftime(date_obj, '%B %Y')
            day = datetime.strftime(date_obj, '%d').lstrip('0')
            return [date, day]

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
        while True:
            for i in range(len(list)): print(f'{i+1}: {list[i]}')
            choice = user_input([str(i) for i in range(1, len(list) + 1)])
            print(f'You chose {list[int(choice)-1]}. Confirm? (Y/N)', end=' ')
            if user_input(['y','n']) == 'y': 
                choices.append(list[int(choice)-1])
                break
    print('Do you have any subvenue to specify? The bot will book all the courts in the table for the time slots if no subvenue is specified. (e.g. which multi-purpose court, badminton court...) (Y/N)', end=' ')
    if user_input(['y','n']) == 'y':
        count = 1
        engine = inflect.engine()
        subvenue_list = []
        while True:
            print('Subvenue needs to be entered exactly as it would appear in REBOKS (capitals, spaces). Copy and paste from REBOKS table if possible.')
            subvenue = input(f'Enter {engine.ordinal(count)} subvenue: ').strip()
            subvenue_list.append(subvenue)
            print('Are there any further subvenues to be added? (Y/N)')
            if user_input(['y','n']) == 'n':
                choices.append(subvenue_list)
                break
            else: count+= 1
    else:
        choices.append([])
    return choices

# prompts and returns a string of the remark to be entered at the shopping cart page
def set_target_remark():
    print('Finally, input the remark to be inserted into the textbox at the shopping cart page.')
    while True:
        remark = input('Remark: ')
        print('Confirm? (Y/N)', end=' ')
        if user_input(['y','n']) == 'y': return remark

# given a APScheduler job object and the booking number, pretty prints the booking's options (selected by user previously)
def print_job(job, i):
    variables = job.args
    print(f'''
    BOOKING {i}
    To be booked on: {variables[0][0]}, {variables[0][1]}
    Date: {variables[2]} {variables[1]}
    Time(s): ''', end='')
    for j in range(len(variables[8])):
        print(f'{variables[8][j]}-{variables[9][j]} | ', end='')
    print(f'''
    Filter 1: {variables[3]}
    Filter 2: {variables[4]}
    Activity: {variables[5]}
    Venue: {variables[6]}
    Subvenue(s): ''', end='')
    for j in range(len(variables[7])):
        print(f'{variables[7][j]} | ', end='')
    print(f'''
    Remark: {variables[10]}
    \n''')

# prompts user for booking number to delete, and deletes that booking based on the unique job ID (the creation time)
def delete_booking(scheduler):
    jobs = scheduler.get_jobs()
    if len(jobs) != 0:
        print('These are your upcoming bookings:')
        time.sleep(1)
        i = 1
        for job in jobs:
            print_job(job, i)
            i += 1
    else:
        print('You have no upcoming bookings! Make a new booking')
        time.sleep(1)
        return
    print('Enter the booking number of the booking to be deleted (e.g. BOOKING 3 -> enter 3):', end=' ')
    del_booking_index = int(user_input([str(i) for i in range(1, len(jobs) + 1)]))
    print_job(jobs[del_booking_index-1], del_booking_index)
    print('Delete this upcoming booking? (Y/N)', end=' ')
    if user_input(['y','n']) == 'y':
        scheduler.remove_job(jobs[del_booking_index-1].id)
        print('Removed booking!')
        time.sleep(1)
    print('''
    1. Delete another booking
    2. Return to menu
    ''')
    if user_input(['1','2']) == '1':
        delete_booking(scheduler)
    else:
        return

# pretty prints upcoming bookings, separating them into jobs tomorrow and those later than tomorrow
def check_pending_bookings(scheduler):
    jobs = scheduler.get_jobs()
    if len(jobs) != 0:
        print('These are your upcoming bookings in the next 24h:')
        time.sleep(1)
        jobs_tmr = []
        jobs_after_tmr = []
        i = 1
        for job in jobs:
            if job.next_run_time.date() <= (datetime.today() + timedelta(days=1)).date():
                jobs_tmr.append(job)
                print_job(job, i)
                i += 1
            else:
                jobs_after_tmr.append(job)
        if len(jobs_after_tmr) != 0:
            print('Would you like to see the rest of your bookings? (Y/N)', end=' ')
            if user_input(['y','n']) == 'y':
                for job in jobs_after_tmr:
                    print_job(job, i)
                    i += 1
        else: time.sleep(1)
    else:
        print('You have no upcoming bookings! Make a new booking')
        time.sleep(1)
        return

    print('''
    1. Start waiting to book
    2. Return to previous menu
    ''')
    if user_input(['1','2']) == '1':
        if len(jobs_tmr) == 0:
            print('You have no booking to be made tomorrow! Make a new booking')
            time.sleep(1)
            return
        else:
            print(f'Started! {len(jobs_tmr)} booking(s) will be made within the next 24h')
            print('Remember to make sure your PC does not sleep or shut down!!!')
            time.sleep(2)
            print('You can use Ctrl+C to exit this process once the booking has been made.\n')
    else:
        return

# MAIN CODE
# initialise APScheduler Background Scheduler
jobstore = {'default': SQLAlchemyJobStore(url=f'sqlite:///{os.path.dirname(os.path.realpath(__file__))}/jobs.sqlite')}
executor = {'default': ThreadPoolExecutor(1)}   # only allow one thread to be run at one time
scheduler = BackgroundScheduler(jobstores=jobstore, executors=executor)
scheduler.start()

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
    print('1. Enter a new booking')
    print('2. Delete a booking')
    print('3. Check pending jobs / start waiting to make the booking')
    print('4. Change login info')
    print('5. Exit')
    response = user_input(['1','2', '3', '4', '5'])
    if response == '1':
        variables = []
        variables.append(set_date_time_to_book_on())
        variables.extend(set_target_date_day())
        variables.extend(set_target_dropdown_lists())
        variables.extend(set_target_time())
        variables.append(set_target_remark())

        # set the time of job to be 2 minutes before (i.e. log in 2 minutes before to wait)
        time_2_min_bef = (datetime.strptime(variables[0][1], '%H%M') - timedelta(minutes=2)).strftime('%H%M')
        scheduler.add_job('main:main', 'date', run_date=datetime.strptime(f'{variables[0][0]} {time_2_min_bef}','%d/%m/%y %H%M'), timezone=pytz.timezone('Singapore'),args=variables, id=datetime.strftime(datetime.now(), '%x %X'), misfire_grace_time=3600)
        print('Added job!')
    elif response == '2':
        delete_booking(scheduler)
    elif response == '3':
        check_pending_bookings(scheduler)
    elif response == '4':
        set_login_info()
    else:
        sys.exit()