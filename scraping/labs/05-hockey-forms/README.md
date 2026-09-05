# Lab 05 — Hockey Teams

**Site:** [scrapethissite.com/pages/forms](https://www.scrapethissite.com/pages/forms/) · **Skill:** a form is a URL · **★** ②

Scrape This Site's forms lesson: NHL team statistics since 1990, behind a search
box and a pager. The page's own brief says what to look for — *"Take a look at
how pagination and search elements change the URL as you browse."*

This is the lab where the browser earns its place, and then stops. You drive the
form **once**, to find out what the form does. After that it is a URL you can
build, and building it is faster, reproducible, and does not depend on a @ref
surviving a re-render.

**Goal:** the teams matching a search, across two pages of results, as CSV.

**Start here**

```bash
h5i browser open https://www.scrapethissite.com/pages/forms/ --session lab05 --new
h5i browser snapshot --session lab05 | grep -i textbox
h5i browser type @e9 "New York" --session lab05
h5i browser submit @e9 --session lab05      # read this answer carefully
```

**Hint:** `submit` tells you the method and the URL it landed on. That URL is
the whole finding.

Then: [`NOTES.md`](NOTES.md).
