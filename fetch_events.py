"""
Fetches candidate weekend events from configured sources:
  1. Ticketmaster Discovery API (family/kids classification)
  2. Any RSS/iCal feeds listed in config.yaml (e.g. library, parks & rec)

Returns a flat list of raw event dicts for score_events.py to filter/rank.
"""
import datetime

import feedparser
import requests
from icalendar import Calendar


def _next_weekend_range():
    """Returns (saturday, sunday) datetime.date for the upcoming weekend."""
    today = datetime.date.today()
    days_until_saturday = (5 - today.weekday()) % 7
    days_until_saturday = days_until_saturday or 7
    saturday = today + datetime.timedelta(days=days_until_saturday)
    sunday = saturday + datetime.timedelta(days=1)
    return saturday, sunday


def fetch_ticketmaster(config):
    tm = config.get("ticketmaster", {})
    api_key = tm.get("api_key")
    if not api_key or api_key.startswith("YOUR_"):
        print("Ticketmaster API key not configured, skipping.")
        return []

    sat, sun = _next_weekend_range()
    params = {
        "apikey": api_key,
        "city": config["location"]["city"],
        "stateCode": config["location"]["state"],
        "radius": config["location"]["radius"],
        "unit": "miles",
        "classificationName": tm.get("classification", "Family"),
        "startDateTime": f"{sat.isoformat()}T00:00:00Z",
        "endDateTime": f"{sun.isoformat()}T23:59:59Z",
        "size": 50,
    }
    resp = requests.get(
        "https://app.ticketmaster.com/discovery/v2/events.json",
        params=params,
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    events = data.get("_embedded", {}).get("events", [])

    results = []
    for e in events:
        venue = ""
        try:
            venue = e["_embedded"]["venues"][0]["name"]
        except (KeyError, IndexError):
            pass
        results.append(
            {
                "source": "Ticketmaster",
                "title": e.get("name"),
                "date": e.get("dates", {}).get("start", {}).get("localDate"),
                "time": e.get("dates", {}).get("start", {}).get("localTime"),
                "venue": venue,
                "url": e.get("url"),
                "description": e.get("info", "") or e.get("pleaseNote", ""),
            }
        )
    return results


def fetch_feeds(config):
    """Pulls events from generic RSS or iCal feeds (library/parks calendars)."""
    results = []
    sat, sun = _next_weekend_range()

    for feed in config.get("feeds", []):
        name, url = feed["name"], feed["url"]
        try:
            if url.endswith(".ics"):
                results.extend(_parse_ical(name, url, sat, sun))
            else:
                results.extend(_parse_rss(name, url, sat, sun))
        except Exception as exc:
            print(f"Skipping feed '{name}' ({url}): {exc}")
    return results


def _parse_rss(name, url, sat, sun):
    parsed = feedparser.parse(url)
    results = []
    for entry in parsed.entries:
        published = getattr(entry, "published_parsed", None)
        if published:
            entry_date = datetime.date(*published[:3])
            if not (sat <= entry_date <= sun):
                continue
        results.append(
            {
                "source": name,
                "title": entry.get("title"),
                "date": entry.get("published", ""),
                "time": "",
                "venue": name,
                "url": entry.get("link"),
                "description": entry.get("summary", ""),
            }
        )
    return results


def _parse_ical(name, url, sat, sun):
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    cal = Calendar.from_ical(resp.content)
    results = []
    for component in cal.walk():
        if component.name != "VEVENT":
            continue
        dtstart = component.get("dtstart").dt
        event_date = dtstart.date() if hasattr(dtstart, "date") else dtstart
        if not (sat <= event_date <= sun):
            continue
        results.append(
            {
                "source": name,
                "title": str(component.get("summary")),
                "date": event_date.isoformat(),
                "time": dtstart.strftime("%H:%M") if hasattr(dtstart, "strftime") else "",
                "venue": name,
                "url": str(component.get("url", "")),
                "description": str(component.get("description", "")),
            }
        )
    return results


def fetch_all(config):
    events = []
    events.extend(fetch_ticketmaster(config))
    events.extend(fetch_feeds(config))
    return events
