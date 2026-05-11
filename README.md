jktlug.id: Jakarta Linux Users Group Website
=============================================

This is the website for the [Jakarta Linux Users Group](https://jktlug.id).
It is a static site generated with [Hakyll] and deployed via [Netlify].

This repository was originally forked from the [Tokyo Linux Users Group]
(tlug/tlug.jp) website and is being migrated for Jakarta/Indonesia use.

## Building

The top-level `Test` script does a build, test, and optional release:

    ./Test

Or manually:

    stack build --test
    stack exec site-compiler build

Preview locally:

    stack exec site-compiler watch -- --host 0.0.0.0

Then open http://localhost:8000 in your browser.

## Deployment

Production is done by committing the compiled site to the `gh-pages`
branch. Configure Netlify to serve from that branch.

## Project Structure

- `app/SiteCompiler.hs` — Hakyll compiler rules
- `src/JKTLUG/` — Wiki parser and link fixer modules
- `docroot/` — Static HTML, CSS, images
- `wiki/` — MediaWiki markup content
- `template/` — Hakyll HTML templates
- `_site/` — Generated static output

## Documentation

See the `doc/` directory for developer notes:
- `doc/how-it-works.md` — Architecture walkthrough
- `doc/haskell-basics.md` — Haskell concepts used in this codebase

[Hakyll]: https://jaspervdj.be/hakyll/
[Netlify]: https://www.netlify.com/
[Tokyo Linux Users Group]: https://tlug.jp
