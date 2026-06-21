"""End-to-end tests for the JKTLUG homepage."""


def test_homepage_loads(page):
    page.goto("/")
    assert page.title() == "Jakarta Linux Users Group"


def test_homepage_about_section(page):
    page.goto("/")
    about = page.locator("#about")
    assert about.is_visible()
    assert "Jakarta Linux Users' Group" in about.inner_text()


def test_homepage_navigation_menu(page):
    page.goto("/")
    menu = page.locator("#menu")
    assert menu.is_visible()
    assert page.locator("a[href='/wiki/Main_Page.html']").is_visible()
    assert page.locator("a[href='/wiki/JKTLUG:Organization.html']").is_visible()


def test_homepage_external_link_has_security_attrs(page):
    page.goto("/")
    luma = page.locator("a[href*='luma.com']")
    assert luma.is_visible()
    assert luma.get_attribute("target") == "_blank"
    assert "noopener" in (luma.get_attribute("rel") or "")
