"""End-to-end tests for wiki pages."""


def test_wiki_main_page_loads(page):
    page.goto("/wiki/Main_Page.html")
    assert page.locator(".content").is_visible()
    content = page.locator(".content").inner_text()
    assert "Welcome to the Jakarta Linux Users Group" in content


def test_wiki_organization_page_loads(page):
    page.goto("/wiki/jktlug:organization.html")
    assert page.locator(".content").is_visible()
    heading = page.locator("h1#jktlug_organization")
    assert heading.is_visible()
    assert "JKTLUG Organization" in heading.inner_text()


def test_wiki_pages_have_menu(page):
    page.goto("/wiki/Main_Page.html")
    assert page.locator("#menu").is_visible()
    assert page.locator("#logo img#header-logo").is_visible()


def test_wiki_current_meeting_redirects(page):
    page.goto("/wiki/Current_Meeting.html")
    page.wait_for_url("**/wiki/Meetings:2026:09.html")
    content = page.locator(".content").inner_text()
    assert "Rin" in content
    assert "GNOME translation" in content
    assert "September 27, 2026" in content


def test_wiki_past_meetings_page(page):
    page.goto("/wiki/Meetings.html")
    content = page.locator(".content").inner_text()
    assert "JKTLUG September Meetup" in content
    assert "Debian Day 2026 Jakarta" in content


def test_wiki_past_meeting_detail(page):
    page.goto("/wiki/Meetings:2026:08.html")
    content = page.locator(".content").inner_text()
    assert "Debian Day 2026 Jakarta" in content
    assert "August 29, 2026" in content
    link = page.locator(".content a[href='https://luma.com/bjl868hr']")
    assert link.is_visible()


def test_wiki_supporters_page(page):
    page.goto("/wiki/Supporters.html")
    content = page.locator(".content").inner_text()
    assert "BlankOn Foundation" in content
    assert "blankon.id" in content


def test_wiki_indonesian_main_page_stays_indonesian(page):
    page.goto("/index.id.html")
    page.locator("#menu a[href='/wiki/Main_Page.id.html']").click()
    page.wait_for_url("**/wiki/Main_Page.id.html")
    assert "Selamat datang" in page.locator(".content").inner_text()


def test_wiki_indonesian_current_meeting_redirects(page):
    page.goto("/wiki/Current_Meeting.id.html")
    page.wait_for_url("**/wiki/Meetings:2026:09.id.html")
    content = page.locator(".content").inner_text()
    assert "Tanggal" in content
    assert "Pendaftaran" in content
    assert "Daftar di Luma" in content


def test_wiki_indonesian_supporters_page(page):
    page.goto("/index.id.html")
    page.locator("#menu a[href='/wiki/Supporters.id.html']").click()
    page.wait_for_url("**/wiki/Supporters.id.html")
    content = page.locator(".content").inner_text()
    assert "BlankOn Foundation" in content
    assert "Situs web" in content


def test_wiki_indonesian_language_switch(page):
    page.goto("/wiki/Main_Page.id.html")
    assert page.locator("#lang-en").get_attribute("href") == "/wiki/Main_Page.html"
    assert page.locator("#lang-id").get_attribute("href") == "/wiki/Main_Page.id.html"
