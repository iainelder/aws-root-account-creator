"""
Creates an AWS root account as automatically as possible. Saves the credentials
in the working directory.
"""

import secrets
import string
import traceback
import configparser
import pathlib
import urllib
import io

import requests
from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from IPython.core.debugger import set_trace


def main():

    try:
        config = read_root_user_config()

        creds = generate_credentials()
        save_credentials(creds)

        driver = init_driver()
        create_root_account(driver, creds, config)

    except Exception:  # pylint: disable=broad-except

        traceback.print_exc()

    finally:

        set_trace()
        driver.close()


def read_root_user_config():

    path = pathlib.Path.home().joinpath(".aws", "root_user_config.ini")
    config = configparser.ConfigParser()
    config.read(path)
    return config


def create_root_account(driver, creds, config):

    visit_signup_page(driver)
    submit_account_credentials(driver, creds)
    submit_identifier_captcha(driver)
    submit_contact_information(driver, config["contact_information"])
    submit_billing_information(driver, config["billing_information"])
    confirm_identity(driver, config["identity_verification"])
    select_support_plan(driver)


def init_driver():

    return webdriver.Firefox()


def visit_signup_page(driver):
    driver.get("https://portal.aws.amazon.com/billing/signup")


def submit_account_credentials(driver, creds):

    wait_for_message(driver, "Sign up for AWS")
    set_account_email_address(driver, creds["email_address"])
    set_account_password(driver, creds["password"])
    set_account_name(driver, creds["account_name"])
    hit_continue(driver)


def submit_identifier_captcha(driver):
    """
    FIXME: This doesn't appear reliably enough for me to complete testing it.

    The identifier captcha doesn't always appear. That's why this function
    has a shorter timeout than the default and swallows the timeout exception.
    This seems inelegant, but it's the easiest thing for now. A nicer solution
    could be to wait for each message in a main loop and dispach the function
    it corresponds to if the message appears. That would make the program more
    flexible and perhaps more robust. But it requires refactoring that I don't
    have time for right now.

    Either way, when it does happen, I need a solution. It's different type of
    captcha from the one that reliably appears. So solve_captcha will fail and
    the debugger will start and I can test with the current state.
    """

    try:
        wait_for_message(driver, "For security reasons, we need to verify that account holders are real people.", timeout=10)
        set_captcha_guess(solve_captcha(extract_canvas_captcha(driver)))
        hit_continue()
    except TimeoutException as ex:
        pass


def extract_canvas_captcha(driver):

    canvas = driver.find_element_by_id("captchaCanvas")
    captcha_data_url = driver.execute_script(
        "return arguments[0].toDataURL('image/png')", canvas)
    response = urllib.request.urlopen(captcha_data_url)
    png_file = io.BytesIO(response.read())
    return png_file


def submit_contact_information(driver, info):

    wait_for_message(driver, "Contact Information")
    set_purpose(driver, "Personal")
    set_contact_name(driver, info["name"])
    set_contact_phone_number(driver, info["phone_number"])
    set_country(driver, info["country"])
    set_address_line_1(driver, info["address_line_1"])
    set_address_line_2(driver, info["address_line_2"])
    set_city(driver, info["city"])
    set_state(driver, info["state"])
    set_postal_code(driver, info["postal_code"])
    agree_to_terms(driver)
    hit_continue(driver)


def submit_billing_information(driver, info):

    wait_for_message(driver, "Billing Information")
    set_card_number(driver, info["card_number"])
    set_card_expiry_month(driver, info["card_expiry_month"])
    set_card_expiry_year(driver, info["card_expiry_year"])
    set_card_holder_name(driver, info["card_holder_name"])
    use_contact_address_as_billing_address(driver)
    hit_continue(driver)


def confirm_identity(driver, info):

    wait_for_message(driver, "Confirm your identity")
    set_verification_method(driver, "Text message (SMS)")
    set_verification_phone_country_code(driver, info["phone_country_code"])
    set_verification_phone_number(driver, info["phone_number"])
    set_captcha_guess(driver, solve_captcha(extract_canvas_captcha(driver)))
    hit_continue(driver, button_label="Send SMS")
    wait_for_message(driver, "Verify code")
    set_sms_pin(driver, input("Verify code: "))
    hit_continue(driver)


def select_support_plan(driver):

    wait_for_message(driver, "Select a support plan")
    set_support_plan(driver, "Basic")
    hit_continue(driver, button_label="Complete sign up")


def generate_credentials():
    creds = generate_identifiers()
    creds["password"] = generate_password()
    return creds


def generate_identifiers():

    account_suffix = ''.join(secrets.choice(string.ascii_lowercase) for i in range(6))

    return {
        "email_address": f"iain+awsroot+{account_suffix}@isme.es",
        "account_name": f"isme-root-{account_suffix}"
    }


def generate_password():

    # "Your password must include a minimum of three of the following mix of character types:
    # uppercase, lowercase, numbers, and ! @ # $ % ^ & * () <> [] {} | _+-= symbols."
    # The append ensures that all character classes are represented.
    symbols = "!@#$%^&*()<>[]{}|_+-="
    classes = [string.ascii_uppercase, string.ascii_lowercase, string.digits, symbols]
    password = ''.join(secrets.choice(''.join(classes)) for i in range(8))
    password += ''.join(map(secrets.choice, classes))
    return password


def save_credentials(creds):

    file_name = "credentials-{account_name}.txt".format_map(creds)

    with open(file_name, "w") as out:

        csv = "{account_name},{email_address},{password}\n".format_map(creds)
        out.write(csv)


def wait_for_message(driver, message, timeout=60):

    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, f"//*[text() = '{message}']")))


def hit_continue(driver, button_label="Continue"):

    # Use submit() function to avoid "not clickable" errors because of the
    # button being obscured.
    button = driver.find_element_by_xpath(f"//button[contains(span/text(), '{button_label}')]")
    button.submit()


def set_account_email_address(driver, address):
    set_text(driver, "email", address)


def set_account_password(driver, password):
    set_text(driver, "password", password)
    set_text(driver, "rePassword", password)


def set_account_name(driver, name):
    set_text(driver, "accountName", name)


def set_purpose(driver, purpose):
    set_radio(driver, "accountType", purpose)


def set_contact_name(driver, name):
    set_text(driver, "address.fullName", name)


def set_country(driver, country):
    set_dropdown(driver, "address.country", country)


def set_contact_phone_number(driver, number):
    set_text(driver, "address.phoneNumber", number)


def set_address_line_1(driver, line):
    set_text(driver, "address.addressLine1", line)


def set_address_line_2(driver, line):
    set_text(driver, "address.addressLine2", line)


def set_city(driver, city):
    set_text(driver, "address.city", city)


def set_state(driver, state):
    set_text(driver, "address.state", state)


def set_postal_code(driver, code):
    set_text(driver, "address.postalCode", code)


def agree_to_terms(driver):
    set_checkbox(driver, "agreement")


def set_card_number(driver, number):
    set_text(driver, "cardNumber", number)


def set_card_expiry_month(driver, month):
    set_dropdown(driver, "expirationMonth", month)


def set_card_expiry_year(driver, year):
    set_dropdown(driver, "expirationYear", year)


def set_card_holder_name(driver, name):
    set_text(driver, "accountHolderName", name)


def use_contact_address_as_billing_address(driver):
    set_radio(driver, "addressType", "Use my contact address")


def set_verification_method(driver, method):
    set_radio(driver, "divaMethod", method)


def set_verification_phone_country_code(driver, country_code):
    set_dropdown(driver, "country", country_code)


def set_verification_phone_number(driver, number):
    set_text(driver, "phoneNumber", number)


def set_sms_pin(driver, pin):
    set_text(driver, "smsPin", pin)


def set_support_plan(driver, plan):
    set_radio(driver, "awsui-tiles-6", plan)


def set_captcha_guess(driver, guess):
    set_text(driver, "captchaGuess", guess) 


def extract_img_captcha(driver):
    img = driver.find_element_by_xpath("//img[@alt='captcha']")
    src = img.get_attribute("src")
    response = requests.get(src, stream=True)
    return requests.raw


def solve_captcha(captcha_file):
    show_image(captcha_file)
    return input("Type the characters shown above: ")


def set_dropdown(driver, element_id, option):

    dropdown = driver.find_element_by_xpath(f"//awsui-select[@id='{element_id}']")
    dropdown.click()
    option = dropdown.find_element_by_xpath(
        f"//*[contains(@id, 'dropdown-option')]//span[text() = '{option}']")
    option.click()


def set_text(driver, input_name, value):

    field = driver.find_element_by_name(input_name)
    field.clear()
    field.send_keys(value)


def set_radio(driver, input_name, label):

    field = driver.find_element_by_xpath(
        f"//div[@class = 'awsui-radio-button' and .//span[contains(text(), '{label}')]]"
        f"//input[@name = '{input_name}']")
    field.send_keys(" ")


def set_checkbox(driver, input_name, selected=True):

    checkbox = driver.find_element_by_name(input_name)

    current = checkbox.is_selected()
    desired = selected

    if current != desired:
        checkbox.send_keys(" ")


def show_image(image_file):

    with Image.open(image_file) as i:
        i.show()


if __name__ == '__main__':
    main()
