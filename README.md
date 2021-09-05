# Automatic creation of AWS root account

Creates a new AWS root account and saves the credentials locally.

The account is for personal use. The billing address is assumed to be the same as the contact address.

Your phone number will verified via SMS. AWS also supports verification by call but the tool does not implement this.

You will be asked to solve at least one captcha to prove your humanity. It will be shown in a new window and you will be prompted for text input in the terminal.

The script is likely to break because of changes to the captcha process especially and changes to the layout and the registration process in general.

To configure the account (see below for format and example):

```
vim ~/.aws/root_user_config.ini
```

To run:

```
pipenv run python main.py
```

To get credentials:

```
cat credentials-*.txt
```

To remove the config:

```
rm ~/.aws/root_user_config.ini
```

## Config Format

The country name, the card expiry month, and the phone country code are selected from a drop-down list. The value must be written exactly as it would be displayed in the list.

Save the config file to `~/.aws/root_user_config.ini` to make it available to the tool.

As the config contains potentially sensitive information, you might want to delete the file after creating the account and saving the content somewhere more secure such as a 1Password vault.

```ini
[contact_information]
name = José García
phone_number = +34612345678
country = Spain
address_line_1 = Calle Equis, 1
address_line_2 = Ático 1ª
city = Barcelona
state = Barcelona
postal_code = 08001

[billing_information]
card_number = 4111111111111111
card_expiry_month = January
card_expiry_year = 2030
card_holder_name = José García

[identity_verification]
phone_country_code = Spain (+34)
phone_number = 657430675
```

## Development

Use flake8 to check code style.

```bash
pipenv run flake8 --extend-ignore=E501
```

Use pylint to also check code style and detect possible errors.

```bash
pipenv run pylint main.py --disable=C0116
```

## References

Using pipenv for isolated dependencies in a structured format

https://docs.python-guide.org/dev/virtualenvs/

Using Selenium to automate brower interaction to create a new account. There is no API for this.

https://www.scrapingbee.com/blog/selenium-python/

Trying to wait for page elements to load

https://selenium-python.readthedocs.io/waits.html

Using REPL in a script

https://stackoverflow.com/questions/1395913/how-to-drop-into-repl-read-eval-print-loop-from-python-code

Show an image

https://stackoverflow.com/questions/35286540/display-an-image-with-python

Load image from URL

https://stackoverflow.com/questions/7391945/how-do-i-read-image-data-from-a-url-in-python

XPath injection. I don't know how to avoid this in Selenium. Is there something like SQL's prepared statements?

https://owasp.org/www-community/attacks/XPATH_Injection

A neater way to select siblings in XPath

https://stackoverflow.com/questions/3139402/how-to-select-following-sibling-xml-tag-using-xpath

How to save a canvas as PNG in Selenium?

https://stackoverflow.com/a/38318578/111424

Configuring Python Projects with INI, TOML, YAML, and ENV files
https://hackersandslackers.com/simplify-your-python-projects-configuration/

## Related Projects

[AWS Account Controller](https://github.com/iann0036/aws-account-controller) provides self-service creation and deletion of sandbox-style accounts in an organization.

[Disposable Cloud Environment](https://github.com/Optum/dce) leases from an existing pool of AWS accounts for a defined period of time and with a limited budget.

[Ubot Studio](http://network.ubotstudio.com/forum/index.php?/topic/21473-amazon-uk-captcha/) can be used to process Amazon's opfcaptcha service.

[aws-generate-account-policy-password](https://github.com/barnesrobert/aws-generate-account-policy-password) is an AWS Python tool for generating a random password that complies with an AWS account's password policy.

[coto](https://github.com/sentialabs/coto/tree/master) provides a client for the undocumented APIs that are used by the AWS Management Console.

# Captcha Solvers

https://2captcha.com/, used by AWS Account Controller

https://www.deathbycaptcha.com/, mentioned on Ubot Studio thread.
