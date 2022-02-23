
# Facility Booking Bot

A Python script built to automatically book NUS facilities according to user's choices beforehand.

Built with the purpose of:

1. Higher success of successful bookings with faster clicks  
2. Removing the need to be present at the exact time when the facility is open for booking 


## Installation
1. Download the repository from Github.  
2. Check your Chrome version by clicking the 3 dots at the top right in Chrome, Help, then About Google Chrome. Download the appropriate web driver for Chrome from https://chromedriver.chromium.org/downloads      
    2.1 Move the chromedriver.exe file to the same folder as the downloaded repository.
3. Go to https://www.python.org/downloads/ to download Python (if you do not have Python installed yet).
4. Go to the folder that contains the program files.  
    4.1 **Mac**: Follow the instructions on https://www.maketecheasier.com/launch-terminal-current-folder-mac/ to open Terminal  
    4.2 **Windows**: Type 'cmd' on the address bar of the Windows Explorer window of the current folder.
5. In Terminal (Mac) or CMD (Windows), type:
    ```
    pip install -r requirements.txt

    // try this for Windows if the above does not work
    py -m pip install -r requirements.txt
    ```

## Usage

```
python3 RUNME.py
py RUNME.py

```
You might need to update your version of Chrome web driver if it is inside the directory but an error saying it does not exist pops up.

This is the main menu that would pop up:
```
1. Enter a new one-time booking
2. Enter a new recurring booking
3. Delete a booking
4. Check pending jobs / start waiting to make the booking
5. Change login info
6. Exit
```

From the main menu, use option 1 or 2 to specify the details of a new upcoming booking. Option 2 would create a **weekly recurring** booking.

The options correspond to the options and dropdown lists to be clicked on the website. Specify the time the booking should be made (usually 0900 or 2100).

Select option 4 **before the specified booking time**. This could be selected much earlier, with the computer prevented from sleeping / shutting down for the booking to occur unattended.

Use Ctrl+C or the options in the menu to exit the program.

**Recurring bookings will be erased once a booking fails for one week!**

## Tech

Libraries/Framework: Selenium WebDriver  
Language: Python

RUNME.py: logic for user selection of booking options  
scheduler.py: schedules, prints, deletes bookings; waits and starts the job when the specified time is reached  
main.py: uses Selenium WebDriver to select options on the booking pages