from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from datetime import datetime, timedelta
import pytz
import os
import time

def main(args=None, check_pending_bookings_bool=False, delete_booking_bool=False):
    jobstore = {'default': SQLAlchemyJobStore(url=f'sqlite:///{os.path.dirname(os.path.realpath(__file__))}/jobs.sqlite')}
    executor = {'default': ThreadPoolExecutor(1)}   # only allow one thread to be run at one time
    scheduler = BackgroundScheduler(jobstores=jobstore, executors=executor)
    scheduler.start()
    if args is not None:
        add(args, scheduler)
    elif check_pending_bookings_bool:
        check_pending_bookings(scheduler)
    elif delete_booking_bool:
        delete_booking(scheduler)

def add(args, scheduler):
    # set the time of job to be 2 minutes before (i.e. log in 2 minutes before to wait)
    time_2_min_bef = (datetime.strptime(args[1][1], '%H%M') - timedelta(minutes=2)).strftime('%H%M')
    scheduler.add_job('main:main', 'date', run_date=datetime.strptime(f'{args[1][0]} {time_2_min_bef}','%d/%m/%y %H%M'), timezone=pytz.timezone('Singapore'), args=args, id=datetime.strftime(datetime.now(), '%x %X'), misfire_grace_time=3600)
    print('Added job!')

def user_input(allowed_responses):
    while True:
        response = input().lower()
        if response in allowed_responses:
            return response
        else:
            print('Invalid response!')

# given a APScheduler job object and the booking number, pretty prints the booking's options (selected by user previously)
def print_job(job, i):
    variables = job.args
    activity_date_obj = datetime.strptime(variables[1][0], '%d/%m/%y').date() + variables[2]
    activity_date = datetime.strftime(activity_date_obj, '%d/%m/%y')
    print(f'''
    BOOKING {i}
    Recurring weekly?: {'Yes' if variables[0] else 'No'}
    To be booked on: {variables[1][0]}, {variables[1][1]}
    Date: {activity_date}
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
            while True:
                time.sleep(10)
    else:
        return

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
        return delete_booking(scheduler)
    else:
        return