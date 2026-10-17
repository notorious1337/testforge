import os

import pytest
from playwright.sync_api import Page, expect


BASE_URL = os.getenv("SAUCEDEMO_URL", "https://www.saucedemo.com/")
USERNAME = os.getenv("SAUCEDEMO_USERNAME", "standard_user")
PASSWORD = os.getenv("SAUCEDEMO_PASSWORD", "secret_sauce")


def login(page: Page) -> None:
    page.goto(BASE_URL)
    page.get_by_placeholder("Username").fill(USERNAME)
    page.get_by_placeholder("Password").fill(PASSWORD)
    page.get_by_role("button", name="Login").click()
    expect(page.locator(".inventory_list")).to_be_visible()


@pytest.mark.playwright
@pytest.mark.smoke
def test_login_and_inventory(page: Page) -> None:
    login(page)
    assert page.url.endswith("/inventory.html")
    expect(page.locator(".inventory_item")).to_have_count(6)


@pytest.mark.playwright
def test_invalid_login(page: Page) -> None:
    page.goto(BASE_URL)
    page.get_by_placeholder("Username").fill("invalid_user")
    page.get_by_placeholder("Password").fill("wrong_password")
    page.get_by_role("button", name="Login").click()

    expect(page.locator("[data-test='error']")).to_contain_text(
        "Username and password do not match"
    )


@pytest.mark.playwright
@pytest.mark.smoke
def test_cart_and_checkout(page: Page) -> None:
    login(page)
    page.locator("[data-test='add-to-cart-sauce-labs-backpack']").click()

    expect(page.locator(".shopping_cart_badge")).to_have_text("1")
    page.locator(".shopping_cart_link").click()
    assert page.url.endswith("/cart.html")

    expect(page.locator(".cart_item")).to_have_count(1)
    expect(page.get_by_text("Sauce Labs Backpack")).to_be_visible()

    page.get_by_role("button", name="Checkout").click()
    page.get_by_placeholder("First Name").fill("Test")
    page.get_by_placeholder("Last Name").fill("User")
    page.get_by_placeholder("Zip/Postal Code").fill("560001")
    page.get_by_role("button", name="Continue").click()

    expect(page.locator(".checkout_summary_container")).to_be_visible()
    expect(page.get_by_text("Sauce Labs Backpack")).to_be_visible()
