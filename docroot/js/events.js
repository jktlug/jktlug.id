/*
 * Renders /data/events.json into the homepage, splitting events into
 * "upcoming" and "past" based on the visitor's current time.
 *
 * Containers (any page may include either one):
 *   <div id="events-upcoming"> ... static fallback ... </div>
 *   <div id="events-past"> ... static fallback ... </div>
 *
 * For previewing, `?now=2026-11-01T00:00:00+07:00` overrides the clock.
 */
(function () {
    "use strict";

    var upcomingEl = document.getElementById("events-upcoming");
    var pastEl = document.getElementById("events-past");
    if (!upcomingEl && !pastEl) return;

    var PAST_LIMIT = 6;
    var TZ = "Asia/Jakarta";
    var lang = /\.id\.html$/.test(window.location.pathname) ? "id" : "en";

    var T = {
        en: {
            locale: "en-US",
            details: "Event details",
            register: "Register on Luma",
            eventPage: "Event page",
            none: "No upcoming events have been announced yet. Follow our Telegram or Matrix group for the next meetup.",
            happening: "Happening now",
            more: "See all past meetings"
        },
        id: {
            locale: "id-ID",
            details: "Detail acara",
            register: "Daftar di Luma",
            eventPage: "Halaman acara",
            none: "Belum ada acara mendatang yang diumumkan. Ikuti grup Telegram atau Matrix kami untuk info meetup berikutnya.",
            happening: "Sedang berlangsung",
            more: "Lihat semua pertemuan sebelumnya"
        }
    }[lang];

    function now() {
        var m = /[?&]now=([^&]+)/.exec(window.location.search);
        if (m) {
            var d = new Date(decodeURIComponent(m[1]));
            if (!isNaN(d)) return d;
        }
        return new Date();
    }

    function text(v) {
        if (v && typeof v === "object") return v[lang] || v.en || "";
        return v || "";
    }

    // End of event: explicit `end`, else end of the start day in WIB.
    function endOf(ev) {
        if (ev.end) return new Date(ev.end);
        var day = new Date(ev.start).toLocaleDateString("en-CA", { timeZone: TZ });
        return new Date(day + "T23:59:59+07:00");
    }

    function fmtDate(d, withWeekday) {
        var opts = { timeZone: TZ, year: "numeric", month: "long", day: "numeric" };
        if (withWeekday) opts.weekday = "long";
        return d.toLocaleDateString(T.locale, opts);
    }

    function fmtTime(d) {
        return d.toLocaleTimeString(T.locale, {
            timeZone: TZ, hour: "2-digit", minute: "2-digit", hourCycle: "h23"
        });
    }

    function el(tag, cls, content) {
        var e = document.createElement(tag);
        if (cls) e.className = cls;
        if (content != null) e.textContent = content;
        return e;
    }

    function link(href, label, external) {
        var a = el("a", null, label);
        a.href = href;
        if (external) {
            a.target = "_blank";
            a.rel = "noopener";
        }
        return a;
    }

    function wikiHref(ev) {
        return "/wiki/" + ev.wiki + (lang === "id" ? ".id.html" : ".html");
    }

    function upcomingCard(ev, current) {
        var start = new Date(ev.start);
        var card = el("div", "event-card");
        card.setAttribute("data-event-id", ev.id);
        var details = el("div", "event-details");
        if (current) details.appendChild(el("p", "event-badge", T.happening));
        details.appendChild(el("h3", null, text(ev.title)));

        var meta = fmtDate(start, true) + " · " + fmtTime(start);
        if (ev.end) meta += "–" + fmtTime(new Date(ev.end));
        meta += " WIB";
        details.appendChild(el("p", "event-meta", meta));
        if (ev.venue) details.appendChild(el("p", "event-venue", text(ev.venue)));

        var links = el("p", "event-register");
        if (ev.wiki) links.appendChild(link(wikiHref(ev), T.details));
        if (ev.register) {
            if (ev.wiki) links.appendChild(document.createTextNode(" · "));
            links.appendChild(link(ev.register, T.register, true));
        }
        if (links.childNodes.length) details.appendChild(links);

        card.appendChild(details);
        return card;
    }

    function pastItem(ev) {
        var li = el("li");
        li.setAttribute("data-event-id", ev.id);
        var title = ev.wiki
            ? link(wikiHref(ev), text(ev.title))
            : ev.register ? link(ev.register, text(ev.title), true) : el("span", null, text(ev.title));
        li.appendChild(title);
        li.appendChild(el("span", "past-date", " — " + fmtDate(new Date(ev.start), false)));
        return li;
    }

    function render(events) {
        var t = now().getTime();
        var upcoming = [], past = [];
        events.forEach(function (ev) {
            if (!ev || !ev.start || isNaN(new Date(ev.start))) return;
            (endOf(ev).getTime() <= t ? past : upcoming).push(ev);
        });
        upcoming.sort(function (a, b) { return new Date(a.start) - new Date(b.start); });
        past.sort(function (a, b) { return new Date(b.start) - new Date(a.start); });

        if (upcomingEl) {
            upcomingEl.textContent = "";
            if (upcoming.length) {
                upcoming.forEach(function (ev) {
                    upcomingEl.appendChild(upcomingCard(ev, new Date(ev.start).getTime() <= t));
                });
            } else {
                upcomingEl.appendChild(el("p", "event-empty", T.none));
            }
        }

        if (pastEl) {
            pastEl.textContent = "";
            var ul = el("ul", "past-events");
            past.slice(0, PAST_LIMIT).forEach(function (ev) { ul.appendChild(pastItem(ev)); });
            if (ul.childNodes.length) pastEl.appendChild(ul);
            var more = el("p", "past-more");
            more.appendChild(link(lang === "id" ? "/wiki/Meetings.id.html" : "/wiki/Meetings.html", T.more));
            pastEl.appendChild(more);
        }
    }

    fetch("/data/events.json", { cache: "no-cache" })
        .then(function (r) {
            if (!r.ok) throw new Error("HTTP " + r.status);
            return r.json();
        })
        .then(function (data) { render(data.events || []); })
        .catch(function () { /* keep the static fallback markup */ });
})();
