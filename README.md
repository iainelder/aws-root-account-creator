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
[account_credentials]
root_user_email_address = jose.garcia+awsroot+${random}@example.org
aws_account_name = test-org-${random}

[contact_information]
name = José García
phone_country_code = Spain (+34)
phone_number = 612345678
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
pipenv run pylint main.py --disable=C0116,W0511
```

See [References.md](References.md) for articles that helped me during development.

## Related Projects

[AWS Account Controller](https://github.com/iann0036/aws-account-controller) provides self-service creation and deletion of sandbox-style accounts in an organization.

[Disposable Cloud Environment](https://github.com/Optum/dce) leases from an existing pool of AWS accounts for a defined period of time and with a limited budget.

[AWS Management Account Vending Machine (MAVM)]() Create new AWS management accounts on the fly and clean up and close accounts afterwards again. It promises to do the same as this tool and more, but [I can't figure out how to make it work](https://github.com/superluminar-io/mavm/issues/43).

[awsapilib](https://github.com/schubergphilis/awsapilib) is a Python library exposing services that are not covered by the official boto3 library but are driven by undocumented APIs. 

[coto](https://github.com/sentialabs/coto/tree/master) provides a client for the undocumented APIs that are used by the AWS Management Console. Similar to awsapilib, but seems to be abandoned.

[aws-generate-account-policy-password](https://github.com/barnesrobert/aws-generate-account-policy-password) is an AWS Python tool for generating a random password that complies with an AWS account's password policy.

# Captcha Solvers

https://2captcha.com/, used by AWS Account Controller

https://www.deathbycaptcha.com/, mentioned on [Ubot Studio thread](http://network.ubotstudio.com/forum/index.php?/topic/21473-amazon-uk-captcha/).
