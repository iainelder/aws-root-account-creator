from pprint import pprint
from time import sleep
from root_console_session import RootConsoleSession, AccessKey
from boto3.session import Session as BotoSession

# TODO: Run mypy, delete existing keys, handle CAPTCHAS, modularize, document, make boto3 dev dependency only.
def main():
    key = create_root_access_key()
    allow_key_to_propagate()
    print_caller_info(key)


def create_root_access_key() -> AccessKey:
    with open("/tmp/pass") as f:
        email,password = f.read().split(",")
    session = RootConsoleSession(
        root_user_email_address=email,
        root_user_password=password,
    )
    key = session.create_access_key()["AccessKey"]

    with open("/tmp/key", "w") as f:
        f.write(f"{key['AccessKeyId']},{key['SecretAccessKey']}")

    return key


def allow_key_to_propagate():
    """Avoid InvalidClientTokenId."""
    print("Wait 10 seconds to allow key to propagate")
    sleep(10)


def print_caller_info(key: AccessKey) -> None:
    session = BotoSession(
        aws_access_key_id=key["AccessKeyId"],
        aws_secret_access_key=key["SecretAccessKey"],
    )
    caller = session.client("sts").get_caller_identity()
    del caller["ResponseMetadata"]
    pprint(caller)


if __name__ == "__main__":
    main()
