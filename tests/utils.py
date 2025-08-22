import random
import string
from typing import Optional


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lowercase()}.com"


def random_lowercase() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=8))


def random_upper_string() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=32))


def random_string() -> str:
    return "".join(random.choices(string.ascii_letters, k=32))


def random_integer() -> int:
    return random.randint(1, 1000)
