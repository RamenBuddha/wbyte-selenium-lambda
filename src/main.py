import logging
import json
import os

#pls work

from tempfile import mkdtemp
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
import time
from datetime import datetime, timedelta, date

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def initialise_driver():
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-pipe")
    chrome_options.add_argument("--verbose")
    chrome_options.add_argument("--log-path=/tmp")
    chrome_options.binary_location = "/opt/chrome/chrome-linux64/chrome"

    service = Service(
        executable_path="/opt/chrome-driver/chromedriver-linux64/chromedriver",
        service_log_path="/tmp/chromedriver.log"
    )

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    return driver


def lambda_handler(event, context):
    driver = initialise_driver()
    pw = os.getenv('PSWD')
    driver.get("https://libcal.uflib.ufl.edu/space/28247")
    logger.info(f"Page title: ${driver.title}")


    # Calculate time two weeks ahead
    d = date.today() + timedelta(days=14)
    dt = datetime(d.year, d.month, d.day, second=0, minute=0, hour=0)
    timestamp = int(datetime.timestamp(dt)* 1000)

    # Go to two weeks ahead
    button = driver.find_element(By.CSS_SELECTOR, ".fc-goToDate-button.btn.btn-default.btn-sm")
    button.click()
    try:
        tdButton = driver.find_element(By.CSS_SELECTOR, f'[data-date="{timestamp}"]')
        tdButton.click()
    except:
        nxt = driver.find_element(By.CSS_SELECTOR, ".next")
        nxt.click()
        tdButton = driver.find_element(By.CSS_SELECTOR, f'[data-date="{timestamp}"]')
        tdButton.click()
    print("Going to correct date...")

    # Wait for the presence of the 'timeframe' elements and then click the second one
    wait = WebDriverWait(driver, 10)  # 10 seconds timeout
    timeframes = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.fc-timeline-event-harness')))
    timeframes[36].click()
    print("Selecting correct time...")

    # Wait for the dropdown to be clickable (or visible, depending on the requirement)
    dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.form-control.input-sm.b-end-date')))
    time.sleep(1)

    # now you can interact with the dropdown
    dropdown = driver.find_element(By.CSS_SELECTOR, '.form-control.input-sm.b-end-date')
    select = Select(dropdown)
    options = select.options
    select.select_by_index(len(options)-1)
    time.sleep(1)

    # Book the times
    submit = driver.find_element(By.CSS_SELECTOR, '[name="submit_times"]')
    submit.click()
    print("Booking the time...")

    # Log in
    wait = WebDriverWait(driver, 120)  # Adjust the timeout as necessary
    username = wait.until(EC.presence_of_element_located((By.ID, 'username')))
    username = driver.find_element(By.ID, 'username')
    username.send_keys("changs@ufl.edu")
    pswd = driver.find_element(By.ID, 'password')
    pswd.send_keys(pw)
    submit = driver.find_element(By.ID, 'submit')
    submit.click()
    print("Logging in...")

    # Wait for Phone Options
    call = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,".button--primary--full-width.button--primary.button--xlarge.undefined")))
    call = driver.find_element(By.CSS_SELECTOR, ".button--primary--full-width.button--primary.button--xlarge.undefined")
    call.click()
    print("Waiting for DUO authentication...")

    # Keep retrying the phone
    timeout = 10
    while True:
        try:
            element_present = EC.presence_of_element_located((By.ID, 'trust-browser-button'))
            WebDriverWait(driver, timeout).until(element_present)
            break
        except TimeoutException:
            other = driver.find_element(By.CSS_SELECTOR, ".button--link ")
            other.click()
            phone = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="test-id-phone"]')))
            phone.click()

        # Wait for Remember Options
        remember = wait.until(EC.element_to_be_clickable((By.ID,"trust-browser-button")))
        remember = driver.find_element(By.ID, "trust-browser-button")
        remember.click()

        element_present = EC.presence_of_element_located((By.CSS_SELECTOR, '[id="fname"]'))
        WebDriverWait(driver, timeout).until(element_present)

        # Submit the final form
        first = driver.find_element(By.CSS_SELECTOR, '[id="fname"]')
        first.send_keys("Eren")
        second = driver.find_element(By.CSS_SELECTOR, '[id="lname"]')
        second.send_keys("Chang")
        check = driver.find_element(By.CSS_SELECTOR, '[id="terms"]')
        check.click()
        submit = driver.find_element(By.CSS_SELECTOR, '[id="btn-form-submit"]')
        submit.click()
        print("Submitting final form...")
        # Gives you time to take a screenshot
        time.sleep(10)
        print("Done!")

    # Quit
        driver.quit()


    body = {
        "title": driver.title
    }

    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }

    return response
