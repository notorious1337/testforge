import os

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = os.getenv("SAUCEDEMO_URL", "https://www.saucedemo.com/")
USERNAME = os.getenv("SAUCEDEMO_USERNAME", "standard_user")
PASSWORD = os.getenv("SAUCEDEMO_PASSWORD", "secret_sauce")


def login(driver: WebDriver) -> None:
    driver.get(BASE_URL)
    driver.find_element(By.ID, "user-name").send_keys(USERNAME)
    driver.find_element(By.ID, "password").send_keys(PASSWORD)
    driver.find_element(By.ID, "login-button").click()
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "inventory_list"))
    )


@pytest.mark.selenium
@pytest.mark.smoke
def test_successful_login(selenium_driver: WebDriver) -> None:
    login(selenium_driver)
    assert "/inventory.html" in selenium_driver.current_url


@pytest.mark.selenium
def test_invalid_login_shows_error(selenium_driver: WebDriver) -> None:
    driver = selenium_driver
    driver.get(BASE_URL)
    driver.find_element(By.ID, "user-name").send_keys("invalid_user")
    driver.find_element(By.ID, "password").send_keys("wrong_password")
    driver.find_element(By.ID, "login-button").click()

    error = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-test='error']"))
    )
    assert "Username and password do not match" in error.text


@pytest.mark.selenium
@pytest.mark.smoke
def test_add_product_to_cart(selenium_driver: WebDriver) -> None:
    driver = selenium_driver
    login(driver)
    driver.find_element(
        By.CSS_SELECTOR, "[data-test='add-to-cart-sauce-labs-backpack']"
    ).click()

    badge = WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "shopping_cart_badge"))
    )
    assert badge.text == "1"

    driver.find_element(By.CLASS_NAME, "shopping_cart_link").click()
    WebDriverWait(driver, 10).until(
        EC.url_contains("/cart.html"),
        message="Cart icon did not navigate to the cart page",
    )
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "cart_list")),
        message="Cart contents did not become visible",
    )
    assert "Sauce Labs Backpack" in driver.page_source
