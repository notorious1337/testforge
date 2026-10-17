import os
from collections.abc import Iterator

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver


@pytest.fixture
def selenium_driver() -> Iterator[WebDriver]:
    options = Options()

    if os.getenv("HEADLESS", "true").lower() == "true":
        options.add_argument("--headless=new")

    chrome_binary = os.getenv("CHROME_BINARY")
    if chrome_binary:
        options.binary_location = chrome_binary

    options.add_argument("--window-size=1440,1000")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    try:
        driver.implicitly_wait(0)
        driver.set_page_load_timeout(30)
        yield driver
    finally:
        driver.quit()
