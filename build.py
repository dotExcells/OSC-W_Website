#!/usr/bin/env python3
"""Build the OSC-W website.

Reads Markdown and YAML from content/, renders it with the templates in
templates/, copies static/ as-is, and writes the finished site to _site/.

Usage:
    python build.py          build the site into _site/
    python build.py serve    build, then preview at http://localhost:8000
"""

import datetime as dt
import shutil
import sys
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
OUT = ROOT / "_site"

MD_EXTENSIONS = ["extra", "sane_lists"]


# ---------------------------------------------------------------- helpers

def read_markdown_file(path):
    """Split a file into (front matter dict, Markdown body)."""
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        meta = yaml.safe_load(front) or {}
    else:
        meta, body = {}, text
    return meta, body.strip()


def md(text):
    return markdown.markdown(text or "", extensions=MD_EXTENSIONS)


def write_page(url, html):
    """Write html so that `url` (e.g. /about/) works on any static host."""
    target = OUT / url.strip("/") / "index.html" if url != "/404.html" else OUT / "404.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def as_date(value):
    if isinstance(value, dt.date):
        return value
    return dt.date.fromisoformat(str(value))


def format_date(value, style="long"):
    # Built by hand rather than with %-d, which doesn't work on Windows.
    d = as_date(value)
    if style == "short":
        return f"{d:%b} {d.day} {d.year}"
    if style == "day":
        return str(d.day)
    if style == "month":
        return f"{d:%b}"
    return f"{d:%A} {d.day} {d:%B} {d.year}"


# ---------------------------------------------------------------- loading

def load_site():
    return yaml.safe_load((CONTENT / "site.yml").read_text(encoding="utf-8"))


def load_data():
    data = {}
    for path in sorted((CONTENT / "data").glob("*.yml")):
        data[path.stem] = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return data


def load_events():
    events = []
    for path in sorted((CONTENT / "events").glob("*.md")):
        if path.name.startswith("_"):
            continue  # _template.md and similar are skipped
        meta, body = read_markdown_file(path)
        missing = [k for k in ("title", "date") if k not in meta]
        if missing:
            sys.exit(f"Event {path.name} is missing: {', '.join(missing)}")
        meta["date"] = as_date(meta["date"])
        meta["slug"] = path.stem
        meta["url"] = f"/event/{path.stem}/"
        meta["content"] = md(body)
        events.append(meta)
    events.sort(key=lambda e: (e["date"], str(e.get("start", ""))))
    return events


def load_pages():
    pages = []
    for path in sorted((CONTENT / "pages").glob("*.md")):
        meta, body = read_markdown_file(path)
        meta.setdefault("template", "page.html")
        meta["content"] = md(body)
        pages.append(meta)
    return pages


# ---------------------------------------------------------------- calendar

def ics_escape(text):
    return (str(text).replace("\\", "\\\\").replace(";", "\\;")
            .replace(",", "\\,").replace("\n", "\\n"))


def build_ics(site, events):
    """A calendar feed people can subscribe to (Outlook, Google, Apple)."""
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0",
        "PRODID:-//OSC-W//Events//EN",
        f"X-WR-CALNAME:{ics_escape(site['title'])} events",
        "X-WR-TIMEZONE:Europe/Amsterdam",
    ]
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for e in events:
        day = e["date"].strftime("%Y%m%d")
        lines += ["BEGIN:VEVENT", f"UID:{e['slug']}@{site['domain']}", f"DTSTAMP:{stamp}"]
        if e.get("start"):
            start = str(e["start"]).replace(":", "")
            end = str(e.get("end", e["start"])).replace(":", "")
            lines += [f"DTSTART;TZID=Europe/Amsterdam:{day}T{start}00",
                      f"DTEND;TZID=Europe/Amsterdam:{day}T{end}00"]
        else:
            lines.append(f"DTSTART;VALUE=DATE:{day}")
        lines.append(f"SUMMARY:{ics_escape(e['title'])}")
        if e.get("location"):
            lines.append(f"LOCATION:{ics_escape(e['location'])}")
        lines.append(f"URL:{site['url']}{e['url']}")
        if e.get("summary"):
            lines.append(f"DESCRIPTION:{ics_escape(e['summary'])}")
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    (OUT / "events.ics").write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")


# ---------------------------------------------------------------- build

def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(STATIC, OUT)

    env = Environment(loader=FileSystemLoader(TEMPLATES),
                      autoescape=select_autoescape(["html"]))
    env.filters["date"] = format_date
    env.filters["markdown"] = md

    site = load_site()
    data = load_data()
    events = load_events()
    today = dt.date.today()
    upcoming = [e for e in events if e["date"] >= today]
    past = list(reversed([e for e in events if e["date"] < today]))

    # Use a self-hosted Open Sans file if one has been added to static/fonts/.
    open_sans = next((f.name for f in sorted((STATIC / "fonts").glob("OpenSans*"))
                      if f.suffix in (".woff2", ".woff", ".ttf")), None)

    common = dict(site=site, data=data, events=events, upcoming=upcoming,
                  past=past, today=today, open_sans_file=open_sans)

    redirects = {}

    for page in load_pages():
        html = env.get_template(page["template"]).render(page=page, **common)
        write_page(page["permalink"], html)
        for alias in page.get("aliases", []):
            redirects[alias] = page["permalink"]

    event_tpl = env.get_template("event.html")
    for e in events:
        write_page(e["url"], event_tpl.render(page=e, event=e, **common))
        for alias in e.get("aliases", []):
            redirects[alias] = e["url"]

    redirect_tpl = env.get_template("redirect.html")
    for old, new in redirects.items():
        write_page(old, redirect_tpl.render(target=new, **common))

    write_page("/404.html", env.get_template("404.html").render(page={"title": "Page not found"}, **common))
    build_ics(site, events)

    print(f"Built {len(events)} events and {len(redirects)} redirects into {OUT.name}/")


def serve():
    import functools
    import http.server
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
    print("Preview at http://localhost:8000  (Ctrl+C to stop)")
    http.server.ThreadingHTTPServer(("localhost", 8000), handler).serve_forever()


if __name__ == "__main__":
    build()
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
