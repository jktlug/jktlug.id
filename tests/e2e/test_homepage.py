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
    page.goto("/?now=2026-11-01T00:00:00%2B07:00")
    upcoming = page.locator("#events-upcoming")
    upcoming.locator(".event-card").first.wait_for()
    text = upcoming.inner_text()
    assert "openSUSE Leap 16.1" in text
    assert "November 7, 2026" in text
    assert "GSIH Spooke 002 (Markas Indonesia)" in text
    assert "10:00–13:15 WIB" in text
    assert upcoming.locator(".event-card").count() == 1
    register = page.locator("#events a[href='https://luma.com/k8impk8a']")
    assert register.is_visible()
    assert register.get_attribute("target") == "_blank"
    assert "noopener" in (register.get_attribute("rel") or "")
    past = page.locator("#events-past")
    assert "JKTLUG September Meetup" in past.inner_text()
    assert "openSUSE" not in past.inner_text()
    page.locator("#events a[href='/wiki/Meetings:2026:11.html']").click()
    page.wait_for_url("**/wiki/Meetings:2026:11.html")
    assert "Nix package manager" in page.locator(".content").inner_text()


def test_homepage_event_moves_to_past_after_it_ends(page):
    page.goto("/?now=2026-11-07T13:16:00%2B07:00")
    page.locator("#events-past li").first.wait_for()
    assert page.locator("#events-upcoming .event-card").count() == 0
    assert page.locator("#events-upcoming .event-empty").is_visible()
    items = page.locator("#events-past li")
    assert "openSUSE Leap 16.1" in items.nth(0).inner_text()
    assert "Debian Day" in items.nth(items.count() - 1).inner_text()


def test_homepage_event_in_progress_stays_upcoming(page):
    page.goto("/?now=2026-11-07T11:00:00%2B07:00")
    badge = page.locator("#events-upcoming .event-badge")
    badge.wait_for()
    assert "openSUSE" in page.locator("#events-upcoming").inner_text()


def test_homepage_indonesian_events(page):
    page.goto("/index.id.html?now=2026-11-01T00:00:00%2B07:00")
    upcoming = page.locator("#events-upcoming")
    upcoming.locator(".event-card").first.wait_for()
    assert "Sabtu, 7 November 2026" in upcoming.inner_text()
    assert "10.00–13.15 WIB" in upcoming.inner_text()
    assert page.locator("#events a[href='/wiki/Meetings:2026:11.id.html']").is_visible()
    assert "Acara Sebelumnya" in page.locator("#past-events").inner_text()


def test_homepage_external_link_has_security_attrs(page):
    page.goto("/")
    matrix = page.locator(".meetings a[href*='matrix.to']")
    assert matrix.is_visible()
    assert matrix.get_attribute("target") == "_blank"
    assert "noopener" in (matrix.get_attribute("rel") or "")


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
