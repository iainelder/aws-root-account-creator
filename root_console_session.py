from dataclasses import dataclass, field

from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import Literal, TypedDict

UserType = Literal["rootUser", "iamUser"]


class AccessKey(TypedDict):
    AccessKeyId: str
    SecretAccessKey: str


@dataclass
class RootConsoleSession:

    root_user_email_address: str
    root_user_password: str
    driver: webdriver.Firefox = field(default_factory=webdriver.Firefox)

    def __post_init__(self) -> None:
        self.log_into_console(self.root_user_email_address, self.root_user_password)

    def log_into_console(
        self,
        root_user_email_address: str,
        root_user_password: str, 
    ) -> None:

        self.go_to("https://us-east-1.console.aws.amazon.com/console/home")
        self.wait_for_message("Sign in")
        self.set_user_type("rootUser")
        self.set_root_user_email_address(root_user_email_address)
        self.hit_button("Next")
        self.wait_for_message("Root user sign in")
        self.set_root_user_password(root_user_password)
        self.hit_button("Sign in")
        self.wait_for_message("Console Home")
        self.accept_cookies()

    def accept_cookies(self) -> None:
        self.hit_button("Accept all cookies")

    def create_access_key(self) -> AccessKey:
        """Creates a new access key for the root user.

        Uses the same response format as the CreateAccessKey CLI.
        https://docs.aws.amazon.com/cli/latest/reference/iam/create-access-key.html
        """
        
        self.go_to("https://us-east-1.console.aws.amazon.com/iamv2/home?region=us-east-1#/security_credentials")
        self.wait_for_clickable_button("Create access key")
        self.scroll_to_element(self.button("Create access key"))
        self.hit_button("Create access key")
        self.set_checkbox("ack-risk")
        self.hit_button("Create access key")
        self.wait_for_message("Retrieve access key")

        # A "Hide" link replaces the "Show" link upon clicking. Use the "Hide"
        # link to navigate to the data elements to avoid errors of staleness.
        self.driver.find_element(By.LINK_TEXT, "Show").click()
        key_row = self.driver.find_element(By.LINK_TEXT, "Hide").find_element(
            By.XPATH, "./ancestor::tr"
        )
        access_key_id, secret_access_key, _ = key_row.text.split("\n")
        assert "AKIA" in access_key_id

        return {
            "AccessKey": {
                "SecretAccessKey": secret_access_key,
                "AccessKeyId": access_key_id,
            }
        }

    def go_to(self, url: str) -> None:
        self.driver.get(url)

    def scroll_to_element(self, element: WebElement) -> None:

        # Scroll to center so neither header nor footer obscure the button.
        # Clicking an obscured button raises an ElementClickInterceptedException.
        self.driver.execute_script(
            'arguments[0].scrollIntoView({block: "center", inline: "nearest"})',
            element
        )

    def button(self, span_text: str) -> WebElement:
        return self.driver.find_element(
            By.XPATH, f"//button[contains(span/text(), '{span_text}')]"
        )

    def hit_button(self, span_text: str) -> None:

        button = self.driver.find_element(
            By.XPATH, f"//button[contains(span/text(), '{span_text}')]"
        )
        button.click()

    def wait_for_clickable_button(self, span_text: str, timeout: int=60) -> None:

        WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//button[contains(span/text(), '{span_text}')]")
            )
        )

    def wait_for_message(self, message, timeout=60):

        WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//*[text() = '{message}']")
            )
        )

    def set_user_type(self, user_type: UserType) -> None:

        field = self.driver.find_element(
            By.XPATH,
            f"//input[@name = 'userType' and @value = '{user_type}']"
        )
        field.send_keys(" ")
    
    def set_root_user_email_address(self, value: str) -> None:
        self.set_text(
            self.driver.find_element(By.ID, "resolving_input"), value
        )

    def set_root_user_password(self, value: str) -> None:
        self.set_text(
            self.driver.find_element(By.ID, "password"), value
        )

    def set_text(self, textfield: WebElement, value: str) -> None:

        textfield.clear()
        textfield.send_keys(value)

    def set_checkbox(self, input_name, selected=True):

        checkbox = self.driver.find_element(By.NAME, input_name)

        current = checkbox.is_selected()
        desired = selected

        if current != desired:
            checkbox.send_keys(" ")
