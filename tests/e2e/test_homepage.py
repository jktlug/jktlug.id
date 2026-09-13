"""End-to-end tests for the JKTLUG homepage."""


def test_homepage_loads(page):
    page.goto("/")
    assert page.title() == "Jakarta Linux Users Group"


def test_homepage_header_bar(page):
    page.goto("/")
    assert page.locator("#header-bar").is_visible()
    assert "Jakarta Linux Users Group" in page.locator("#site-title").inner_text()
    assert page.locator("#header-bar img#header-logo").is_visible()
    padding = page.evaluate(
        "getComputedStyle(document.querySelector('#header-bar')).paddingLeft"
    )
    assert padding == "200px"
    assert (
        page.evaluate("getComputedStyle(document.querySelector('#site-title')).fontSize")
        == "22px"
    )
    logo_height = page.evaluate(
        "document.querySelector('#header-logo').getBoundingClientRect().height"
    )
    assert round(logo_height) == 70


def test_homepage_about_section(page):
    page.goto("/")
    about = page.locator("#about")
    assert about.is_visible()
    assert "Jakarta Linux Users Group" in about.inner_text()


def test_homepage_navigation_menu(page):
    page.goto("/")
    menu = page.locator("#menu")
    assert menu.is_visible()
    assert page.locator("#menu a[href='/wiki/Main_Page.html']").is_visible()
    assert page.locator(
        "#menu a[href='/wiki/jktlug:organization.html']"
    ).is_visible()
    assert page.locator("#menu a[href='/wiki/Supporters.html']").is_visible()


def test_homepage_upcoming_event(page):
    page.goto("/")
    events = page.locator("#events")
    assert "JKTLUG September Meetup" in events.inner_text()
    assert "September 27, 2026" in events.inner_text()
    assert page.locator("#events .event-date").count() == 0
    assert page.locator("#events a.button").count() == 0
    register = page.locator("#events a[href='https://luma.com/3piobror']")
    assert register.is_visible()
    assert register.get_attribute("target") == "_blank"
    assert "noopener" in (register.get_attribute("rel") or "")


def test_homepage_external_link_has_security_attrs(page):
    page.goto("/")
    luma = page.locator("a[href*='luma.com']")
    assert luma.is_visible()
    assert luma.get_attribute("target") == "_blank"
    assert "noopener" in (luma.get_attribute("rel") or "")


def test_homepage_theme_toggle_cycles(page):
    page.goto("/")
    toggle = page.locator("#theme-toggle")
    assert toggle.is_visible()
    assert toggle.inner_text() == "System"
    toggle.click()
    assert toggle.inner_text() == "Dark"
    assert (
        page.evaluate("document.documentElement.getAttribute('data-theme')") == "dark"
    )
    assert (
        page.evaluate("getComputedStyle(document.body).backgroundColor")
        == "rgb(18, 18, 18)"
    )
    toggle.click()
    assert toggle.inner_text() == "Light"
    assert (
        page.evaluate("document.documentElement.getAttribute('data-theme')") == "light"
    )
    assert (
        page.evaluate("getComputedStyle(document.body).backgroundColor")
        == "rgb(255, 255, 255)"
    )
    toggle.click()
    assert toggle.inner_text() == "System"
    assert (
        page.evaluate("document.documentElement.hasAttribute('data-theme')") is False
    )


def test_homepage_footer_has_no_supporter_credit(page):
    page.goto("/")
    footer = page.locator("#footer")
    assert "BlankOn" not in footer.inner_text()
    assert "All rights reserved" in footer.inner_text()
    assert "2026" in footer.inner_text()


def test_homepage_body_padding(page):
    page.goto("/")
    assert page.evaluate("getComputedStyle(document.body).padding") == "20px"


def test_homepage_respects_system_dark(page):
    page.emulate_media(color_scheme="dark")
    page.goto("/")
    assert (
        page.evaluate("getComputedStyle(document.body).backgroundColor")
        == "rgb(18, 18, 18)"
    )


def test_homepage_mobile_layout(page):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto("/")
    assert page.locator("#header-bar").is_visible()
    assert page.locator("#menu").is_visible()
    assert page.locator(".content").is_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= 390")
    padding = page.evaluate(
        "getComputedStyle(document.querySelector('#header-bar')).paddingLeft"
    )
    assert padding == "16px"


def test_homepage_indonesian_version(page):
    page.goto("/index.id.html")
    content = page.locator(".content").inner_text()
    assert "Acara Mendatang" in content
    assert "Tentang JKTLUG" in content
    assert page.locator("#lang-en").get_attribute("href") == "/index.html"


def test_homepage_indonesian_links_stay_indonesian(page):
    page.goto("/index.id.html")
    assert page.locator("#site-title").get_attribute("href") == "/index.id.html"
    assert page.locator("#logo").get_attribute("href") == "/index.id.html"
    assert page.locator("#menu a[href='/wiki/Supporters.id.html']").is_visible()
    assert page.locator(".content a[href='/wiki/Current_Meeting.id.html']").is_visible()
