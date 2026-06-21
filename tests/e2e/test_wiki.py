"""End-to-end tests for wiki pages."""


def test_wiki_main_page_loads(page):
    page.goto("/wiki/Main_Page.html")
    assert page.locator(".content").is_visible()
    content = page.locator(".content").inner_text()
    assert "Welcome to the Jakarta Linux Users Group" in content


def test_wiki_organization_page_loads(page):
    page.goto("/wiki/JKTLUG:Organization.html")
    assert page.locator(".content").is_visible()
    heading = page.locator("h1#jktlug_organization")
    assert heading.is_visible()
    assert "JKTLUG Organization" in heading.inner_text()


def test_wiki_pages_have_menu(page):
    page.goto("/wiki/Main_Page.html")
    assert page.locator("#menu").is_visible()
    assert page.locator("#logo img#header-logo").is_visible()
