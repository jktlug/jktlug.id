# How the TLUG Website Works

This document explains the architecture of the TLUG website — what
happens when a visitor opens the site, which files and templates are
involved, and how all the pieces fit together.

## Architecture Overview

The site is a **static site generated at build time** using
[Hakyll](https://jaspervdj.be/hakyll/), a Haskell framework. There
is no server-side runtime (no database, no PHP, no application
server). Everything that a visitor sees was compiled ahead of time
into plain HTML/CSS files and deployed to a CDN (Netlify).

```
Source Files  →  Hakyll Compiler  →  _site/  →  Netlify CDN
(docroot/        (Haskell program)    (HTML)     (serves to users)
 wiki/
 template/)
```

## What Happens When You Open the Root URL

When a browser visits `https://tlug.jp/` (or `localhost:8000` locally),
here is the chain of files and transformations that produces the
response:

### Step 1: The Request

The server (Netlify or Hakyll's built-in preview server) looks for
the default document at the path `/`. It finds `_site/index.html`
and returns it.

### Step 2: How `_site/index.html` Was Built

The compiler (`app/SiteCompiler.hs`) matched `docroot/*.html` and
processed `docroot/index.html`. The rule for this match is:

```haskell
match "docroot/*.html" $ do
    route   dropInitialComponent      -- removes "docroot/" prefix
    compile $ pandocCompiler
        >>= loadAndApplyTemplate "template/main.html" defaultContext
```

So:
1. The source file `docroot/index.html` is read.
2. `pandocCompiler` parses it (minimal transformation, since it's
   already HTML).
3. That content is injected into `template/main.html` at the `$body$`
   placeholder.
4. The result is written to `_site/index.html`.

### Step 3: The Template

`template/main.html` is the site-wide wrapper. It contains the full
page structure:

- `<head>` with charset, title, and CSS link (`/css/tlug4.css`)
- The top banner with the TLUG logo and language switcher
- The left-side menu (General, Meetings, Mailing Lists, etc.)
- The `$body$` placeholder where page-specific content goes
- The footer and JavaScript

The content from `docroot/index.html` (the "Coming/Recent Events"
section, "About TLUG", etc.) is inserted where `$body$` appears.

### Step 4: Assets

The browser then requests linked assets:

| Asset | Source | How it's copied |
|-------|--------|----------------|
| `/css/tlug4.css` | `docroot/css/tlug4.css` | `match "docroot/**"` with `copyFileCompiler` |
| `/images/shirt200.png` | `docroot/images/shirt200.png` | Same |
| `/images/tlug-uname.png` | `docroot/images/tlug-uname.png` | Same |

These are copied verbatim from `docroot/**` to `_site/**` by the
compiler.

## The Two Kinds of Content

The site serves two fundamentally different kinds of pages:

### 1. Static Pages (docroot/)

Files in `docroot/` are hand-written static content — mostly HTML,
with some CSS and images. They are copied or lightly processed and
wrapped in `template/main.html`.

**Examples:**
- `docroot/index.html` — English home page
- `docroot/index.ja.html` — Japanese home page
- `docroot/css/`, `docroot/images/` — Static assets

### 2. Wiki Pages (wiki/)

Files in `wiki/` are **MediaWiki markup** from the old website. The
custom `mediawikiCompiler` does a multi-stage transformation:

```
wiki/Some_Page
    │
    ▼
TLUG.MediaWiki.parseFile
    ├── Parse MediaWiki markup → list of Chunks
    ├── Resolve transclusions ({{Template:Foo}})
    ├── Substitute parameters ({{{1}}})
    ├── Read and merge template files
    └── Return ProcPage { body, redirect, categories }
    │
    ▼
Pandoc.readMediaWiki
    └── Convert MediaWiki markup string → Pandoc AST
    │
    ▼
Pandoc.writeHtml
    └── Convert AST → HTML string
    │
    ▼
TLUG.WikiLink.fixWikiLinks
    ├── Fix [[links]] to proper relative URLs
    ├── Resolve images
    ├── Extract categories
    └── Mark broken links in red
    │
    ▼
Hakyll template system
    └── Wrap in template/main.html (or category.html)
    │
    ▼
_site/wiki/Some_Page
```

**Key feature: Transclusion.** MediaWiki templates let a page include
content from another file. For example, `Meetings:2024:03` might
include `{{Template:Meetings:Itinerary:Tech:2024}}`. The compiler
recursively reads and inlines these templates, just like the real
MediaWiki engine did.

**Redirects.** Wiki pages with `#REDIRECT [[Other Page]]` are
converted to HTML redirect pages with `<meta http-equiv="refresh">`.

**Categories.** Pages tagged with `[[Category:Meetings:2024]]` are
tracked by Hakyll's tag system. The compiler generates category
listing pages automatically (e.g., a page showing all meetings from
2024).

## Site Map: File → Router → Output

Here is every rule in `SiteCompiler.hs` and what it does:

| Match Pattern | Route | Compiler | Output Path |
|---|---|---|---|
| `template/*` | — | `templateCompiler` | Loaded into memory only |
| `docroot/*.html` | `dropInitialComponent` | `pandocCompiler` + `template/main.html` | `_site/*.html` |
| `docroot/**` | `dropInitialComponent` | `copyFileCompiler` | `_site/**` |
| `wiki/*` | `idRoute` (keep name) | `mediawikiCompiler` | `_site/wiki/*` |
| `example/**` | various | various | `_site/example/**` |

The `dropInitialComponent` route simply strips the `docroot/`
prefix. So `docroot/index.html` becomes `_site/index.html`.

The `idRoute` for wiki pages keeps the filename exactly as-is. These
files have no extension intentionally; `netlify.toml` tells Netlify
to serve them with `Content-Type: text/html; charset=utf-8`.

## The Netlify Configuration

`docroot/netlify.toml` sets two things:

1. **Content-Type headers for wiki pages:** Files under `/wiki/*` are
   served as HTML, even without a `.html` extension.

2. **Redirect from `/wiki/` to `/wiki/Main_Page`:** Emulates
   MediaWiki's behavior where the wiki root shows the main page.

## Category Pages

The compiler extracts categories from wiki pages and auto-generates
category listing pages:

```haskell
tags <- buildTagsWith wikiCategoryRules "wiki/*" (fromCapture "wiki/*")
createCategoryPages tags
```

- `wikiCategoryRules` reads each wiki file and extracts its
  `[[Category:...]]` tags.
- `createCategoryPages` generates a page for each unique category,
  listing all pages in that category.
- These pages use `template/category.html` for their layout, then
  wrap in `template/main.html`.

## What Happens During `stack exec site-compiler watch`

When you run the preview server locally:

1. Hakyll builds the site once into `_site/`.
2. An HTTP server starts on `localhost:8000` (or your chosen port).
3. Hakyll watches the source directories (`docroot/`, `wiki/`,
   `template/`, etc.) for changes.
4. When a file changes, only the affected outputs are rebuilt.
5. You refresh the browser to see the change.

Note: Hakyll does **not** auto-refresh your browser. You must reload
manually.

## Summary: First-Visit File Chain

When you open `/` in the browser, this is the complete chain:

```
Browser ──GET /──► Server
                         │
                         ▼
                  _site/index.html
                         │
           ┌─────────────┴─────────────┐
           │                             │
    template/main.html           docroot/index.html
    (site structure)             (page content)
           │                             │
           └────────► $body$ ◄──────────┘
                         │
                  _site/index.html
                         │
           ┌─────────────┴─────────────┐
           ▼                             ▼
     docroot/css/tlug4.css       docroot/images/shirt200.png
     docroot/images/tlug-uname.png
```

If you click a link to `/wiki/Meetings:2024:03`, the chain becomes:

```
Browser ──GET /wiki/Meetings:2024:03──► Server
                                           │
                                           ▼
                                    _site/wiki/Meetings:2024:03
                                           │
  ┌────────┬──────────────┬──────────────┬────────┐
  │        │              │              │        │
  ▼        ▼              ▼              ▼        ▼
template  TLUG.MediaWiki  Pandoc  TLUG.WikiLink  template
/main.html  .parseFile   .read/write  .fixWikiLinks /main.html
  │        │              │              │            │
  │        ▼              ▼              ▼            │
  │        Chunks ───► Pandoc AST ───► HTML           │
  │        +Transclusion     +Image/link fixup        │
  │                                                   │
  └────────────────────► $body$ ◄─────────────────────┘
                              │
                    _site/wiki/Meetings:2024:03
                              │
                    template/main.html (wrapped around)
```

The beauty of the static site approach: **all of this complexity
runs once at build time**. The visitor just downloads plain HTML.
