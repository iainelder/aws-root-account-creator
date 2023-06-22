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

from PIL import Image

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from IPython.core.debugger import set_trace


def main():

    try:
        config = read_root_user_config()
        config["account_credentials"]["root_user_password"] = (
            generate_root_user_password()
        )

        save_credentials(config["account_credentials"])

        driver = init_driver()
        create_root_account(driver, config)

    except Exception:  # pylint: disable=broad-except

        traceback.print_exc()

    finally:

        set_trace()
        driver.close()


def read_root_user_config():

    path = pathlib.Path.home().joinpath(".aws", "root_user_config.ini")
    # Interpolation misinterprets certain password characters. All I really need
    # to return is a nest of dicts, but there's no built-in method for that.
    config = configparser.ConfigParser(interpolation=None)
    config.read(path)
    for key, value in config["account_credentials"].items():
        config["account_credentials"][key] = substitute(value)
    return config


def substitute(template_str):
    return string.Template(template_str).substitute(
        random=''.join(secrets.choice(string.ascii_lowercase) for _ in range(6))
    )


def create_root_account(driver, config):

    visit_signup_page(driver)
    submit_account_credentials(driver, config["account_credentials"])
    submit_contact_information(driver, config["contact_information"])
    submit_billing_information(driver, config["billing_information"])
    confirm_identity(driver, config["identity_verification"])
    select_support_plan(driver)


def init_driver():

    return webdriver.Firefox()


def visit_signup_page(driver):
    driver.get("https://portal.aws.amazon.com/billing/signup")


def submit_account_credentials(driver, creds):

    submit_account_identity(driver, creds)
    submit_email_confirmation(driver)
    submit_account_password(driver, creds)


def submit_account_identity(driver, creds):

    wait_for_message(driver, "Sign up for AWS")
    set_account_email_address(driver, creds["root_user_email_address"])
    set_account_name(driver, creds["aws_account_name"])
    hit_continue(driver, "Verify email address")


def submit_email_confirmation(driver):

    wait_for_message(driver, "Confirm you are you")
    set_verification_code(driver, input("Email verification code: "))
    hit_continue(driver, "Verify")


def submit_account_password(driver, creds):

    wait_for_message(driver, "Create your password")
    set_account_password(driver, creds["root_user_password"])
    hit_continue(driver)


def extract_canvas_captcha(driver):

    # FIXME: Often the data URL is taken before the captcha is loaded. When this
    # happens the returned PNG image is blank. Add a wait_for_captcha function
    # or similar.
    canvas = driver.find_element(By.ID, "captchaCanvas")
    captcha_data_url = driver.execute_script(
        "return arguments[0].toDataURL('image/png')", canvas)
    print(f"DEBUG {captcha_data_url=}")
    with urllib.request.urlopen(captcha_data_url) as response:
        png_file = io.BytesIO(response.read())
        return png_file


def submit_contact_information(driver, info):

    wait_for_message(driver, "Contact Information")
    set_purpose(driver, "Personal")
    set_contact_name(driver, info["name"])
    set_contact_phone_country_code(driver, info["phone_country_code"])
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

    # If the prompt appears, choose SMS because it's easier to use manually.
    # If the prompt does not appear, AWS forces you to receive a call.
    # Sometimes the prompt appears, sometimes it doesn't. I don't know why.
    # TODO: Try to automate the call confirmation to avoid this choice.
    wait_for_message(driver, "Confirm your identity")
    body_text = driver.find_element(By.XPATH, "//body").text
    choice_prompt = "How should we send you the verification code?"
    if choice_prompt in body_text:
        confirm_identity_by_sms(driver, info)
    else:
        confirm_identity_by_call(driver, info)


def confirm_identity_by_sms(driver, info):

    wait_for_message(driver, "Confirm your identity")
    set_verification_method(driver, "Text message (SMS)")
    set_verification_phone_country_code(driver, info["phone_country_code"])
    set_verification_phone_number(driver, info["phone_number"])
    set_captcha_guess(driver, solve_captcha(extract_canvas_captcha(driver)))
    hit_continue(driver, button_label="Send SMS")

    wait_for_message(driver, "Verify code")
    set_sms_pin(driver, input("Verify code: "))
    hit_continue(driver)


def confirm_identity_by_call(driver, info):

    raise Exception("Identity confirmation by call not implemented")


def select_support_plan(driver):

    wait_for_message(driver, "Select a support plan")
    set_support_plan(driver, "Basic")
    hit_continue(driver, button_label="Complete sign up")


def generate_root_user_password():

    # "Your password must include a minimum of three of the following mix of character types:
    # uppercase, lowercase, numbers, and ! @ # $ % ^ & * () <> [] {} | _+-= symbols."
    # The append ensures that all character classes are represented.
    symbols = "!@#$%^&*()<>[]{}|_+-="
    classes = [string.ascii_uppercase, string.ascii_lowercase, string.digits, symbols]
    password = ''.join(secrets.choice(''.join(classes)) for i in range(8))
    password += ''.join(map(secrets.choice, classes))
    return password


def save_credentials(creds):

    file_name = "credentials-{aws_account_name}.txt".format_map(creds)

    with open(file_name, "w") as out:

        template = "{aws_account_name},{root_user_email_address},{root_user_password}\n"
        csv = template.format_map(creds)
        out.write(csv)


def wait_for_message(driver, message, timeout=600):

    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.XPATH, f"//*[text() = '{message}']")))


def hit_continue(driver, button_label="Continue"):

    # Use submit() function to avoid "not clickable" errors because of the
    # button being obscured.
    button = driver.find_element(By.XPATH, f"//button[contains(span/text(), '{button_label}')]")
    button.submit()


def set_account_email_address(driver, address):
    set_text(driver, "emailAddress", address)


def set_verification_code(driver, code):
    set_text(driver, "otp", code)


def set_account_password(driver, password):
    set_text(driver, "password", password)
    set_text(driver, "rePassword", password)


def set_account_name(driver, name):
    set_text(driver, "fullName", name)


def set_purpose(driver, purpose):
    set_radio(driver, "accountType", purpose)


def set_contact_name(driver, name):
    set_text(driver, "address.fullName", name)


def set_country(driver, country):
    set_dropdown(driver, "address.country", country)


def set_contact_phone_country_code(driver, code):
    set_dropdown(driver, "address.phoneCode", code)


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


def solve_captcha(captcha_file):
    show_image(captcha_file)
    return input("Type the characters shown above: ")


def set_dropdown(driver, element_id, option):

    dropdown = driver.find_element(By.XPATH, f"//awsui-select[@id='{element_id}']")
    dropdown.click()
    option = dropdown.find_element(By.XPATH, 
        f"//*[contains(@id, 'dropdown-option')]//span[text() = '{option}']")
    option.click()


def set_text(driver, input_name, value):

    field = driver.find_element(By.NAME, input_name)
    field.clear()
    field.send_keys(value)


def set_radio(driver, input_name, label):

    field = driver.find_element(By.XPATH, 
        f"//div[@class = 'awsui-radio-button' and .//span[contains(text(), '{label}')]]"
        f"//input[@name = '{input_name}']")
    field.send_keys(" ")


def set_checkbox(driver, input_name, selected=True):

    checkbox = driver.find_element(By.NAME, input_name)

    current = checkbox.is_selected()
    desired = selected

    if current != desired:
        checkbox.send_keys(" ")


def show_image(image_file):

    with Image.open(image_file) as i:
        i.show()


if __name__ == '__main__':
    main()
