End-to-End Tests
================

The project uses **Python + pytest + Playwright** for end-to-end (e2e)
browser testing of the generated static site. These tests verify that
pages render correctly, navigation works, and key content is visible to
users.


Prerequisites
-------------

- Python 3.9 or later
- `pip3` (usually bundled with Python)
- The static site built in `_site/` (run `./Test` or
  `stack exec site-compiler rebuild` first)


Installation
------------

Install the Python dependencies and Playwright browsers:

```bash
cd tests/e2e
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

The tests use **Chromium** by default. You can also install Firefox or
WebKit if you wish to test against multiple browsers:

```bash
python3 -m playwright install firefox webkit
```


Running Tests
-------------

### Quick start via `./Test`

Build the site and run the e2e tests in one command:

```bash
./Test --e2e
```

### Run only e2e tests (site must already be built)

```bash
tests/e2e/run.sh
```

### Run with pytest directly

```bash
cd tests/e2e
python3 -m pytest
```

### Common pytest options

```bash
# Run in headed mode (see the browser window)
python3 -m pytest --headed

# Run a specific test file
python3 -m pytest test_homepage.py

# Run a specific test
python3 -m pytest test_homepage.py::test_homepage_loads

# Run with the UI inspector (slow motion + inspector)
python3 -m pytest --headed --slowmo 1000

# Generate an HTML report
python3 -m pytest --html=report.html
```


Test Architecture
-----------------

```
_tests/e2e/_
├── conftest.py          # Session-scoped fixtures
├── requirements.txt     # Python dependencies
├── run.sh               # Convenience runner script
├── test_homepage.py     # Tests for docroot/index.html
└── test_wiki.py         # Tests for wiki/*.html pages
```

### `conftest.py`

This file defines a `base_url` fixture that:

1. Verifies `_site/` exists (skips otherwise).
2. Finds a free TCP port on `127.0.0.1`.
3. Starts `python3 -m http.server` to serve `_site/`.
4. Yields the local URL (e.g. `http://127.0.0.1:12345`).
5. Shuts down the server after the test session ends.

Because the fixture has `scope="session"`, the server is started once
and reused for all tests.

### `page` fixture (from pytest-playwright)

`pytest-playwright` provides a `page` fixture that is a Playwright
`Page` object pre-configured with `base_url`. This means you can use
relative URLs:

```python
def test_example(page):
    page.goto("/")                 # -> http://127.0.0.1:PORT/
    page.goto("/wiki/Main_Page.html")
```


Writing New Tests
-----------------

Create a new file named `test_<feature>.py` in `tests/e2e/`:

```python
def test_my_feature(page):
    page.goto("/wiki/My_Page.html")

    # Assert visibility
    assert page.locator("h1").is_visible()

    # Assert text content
    assert "Expected Text" in page.locator(".content").inner_text()

    # Assert element count
    assert page.locator("a").count() > 5
```

### Useful Playwright patterns

| Action | Example |
|---|---|
| Click | `page.locator("button").click()` |
| Fill input | `page.locator("input#name").fill("Alice")` |
| Wait for nav | `page.wait_for_url("**/wiki/Target.html")` |
| Screenshot | `page.screenshot(path="shot.png")` |
| Evaluate JS | `page.evaluate("() => document.title")` |

See the [Playwright Python docs][pw-py] for the full API.


CI / GitLab CI Integration
--------------------------

Playwright browsers can be installed in CI with:

```yaml
test:e2e:
  image: mcr.microsoft.com/playwright/python:v1.45.0-jammy
  script:
    - ./Test --test-only          # build Haskell unit tests
    - stack exec site-compiler rebuild
    - cd tests/e2e && pip3 install -r requirements.txt
    - python3 -m pytest
```

Or, if your CI image does not include Playwright browsers, add:

```yaml
    - python3 -m playwright install chromium
```


Troubleshooting
---------------

### `_site/ does not exist`

Build the site first:

```bash
stack exec site-compiler rebuild
```

### `playwright._impl._errors.Error: Browser not found`

Install the browsers:

```bash
python3 -m playwright install chromium
```

### Port already in use / server timeout

The `conftest.py` fixture picks a random free port automatically. If
you see timeout errors, check that nothing is blocking `127.0.0.1` or
that your firewall does not restrict local loopback connections.

### Headless vs. Headed

By default Playwright runs headless. If a test passes locally but fails
in CI, try running headed locally to debug:

```bash
python3 -m pytest --headed --slowmo 500
```


References
----------

- [pytest-playwright][pytest-pw]
- [Playwright Python API][pw-py]
- [Playwright best practices][pw-best]

<!-------------------------------------------------------------------->
[pytest-pw]: https://playwright.dev/python/docs/pytest-plugin
[pw-py]: https://playwright.dev/python/docs/api/class-page
[pw-best]: https://playwright.dev/python/docs/best-practices
