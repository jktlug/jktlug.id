# Pi Development Plan: JKTLUG Website Migration

## Real Goal

Transform this fork of `tlug/tlug.jp` into the **Jakarta Linux Users
Group (JKTLUG)** website at `jktlug.id`.

## Status (Complete)

- [x] Module renames (TLUG → JKTLUG) — `src/TLUG/` renamed, all imports updated
- [x] Package rename (`tlug-website.cabal` → `jktlug-website.cabal`)
- [x] Homepage rewrite — minimal JKTLUG content in `docroot/index.html`
- [x] Template rewrite — `template/main.html` stripped of TLUG branding
- [x] Wiki content cleanup — all historical TLUG meeting pages removed, `wiki/Main_Page` created with JKTLUG welcome
- [x] Image/CSS rebrand — `tlug4.css` → `jktlug.css`, old TLUG photos removed
- [x] `docroot/index.ja.html` (Japanese homepage) removed
- [x] `example/` directory and its Hakyll rules removed
- [x] `README.md` rewritten for JKTLUG
- [x] Test suite updated (MediaWikiTest.hs stripped of TLUG fixtures)
- [x] Build verified — `./Test` passes, `stack exec site-compiler rebuild` succeeds
- [x] Generated `_site/` verified — no TLUG/Tokyo references in output
- [x] Devcontainer `LANG=C.UTF-8` fix applied to Dockerfile

## Remaining TODOs

- [ ] Create `docroot/images/logo.png` for the JKTLUG logo
- [ ] Replace or remove `images/logo.png` placeholder reference in `template/main.html`
- [ ] Add actual Jakarta meeting content (venues, dates, registration links)
- [ ] Add mailing list / community links once established
- [ ] Rewrite `doc/ORGANIZATION.md`, `doc/proposals.md`, `doc/hosting.md` for JKTLUG
- [ ] Verify Netlify deploy config (`docroot/netlify.toml`) is correct for `jktlug.id`
- [ ] Enable `.github/workflows/main.yaml` if using GitHub Actions deploy
- [ ] Add `docroot/index.id.html` if supporting Bahasa Indonesia language switcher
- [ ] Add JKTLUG-specific wiki pages under `wiki/Meetings:YYYY:MM`

## Quick Reference

| Task | Command |
|---|---|
| Build + test | `./Test` |
| Compile site | `stack exec site-compiler build` |
| Full rebuild | `stack exec site-compiler clean && stack exec site-compiler rebuild` |
| Preview server | `stack exec site-compiler watch -- --host 0.0.0.0` |

## Constraints and Decisions Needed

1. **Language policy:** Does JKTLUG operate in English, Indonesian,
   or both? This affects homepage, templates, and wiki pages.
2. **Meeting cadence:** What's JKTLUG's schedule?
3. **Venues:** Need Jakarta venue names and addresses.
4. **Mailing list:** Does JKTLUG have a mailing list host?
5. **Logo and branding:** Need JKTLUG logo image (PNG) to create `logo.png`.
6. **Registration platform:** Eventbrite, Meetup, or something else?
7. **Domain config:** `jktlug.id` DNS and Netlify setup.
