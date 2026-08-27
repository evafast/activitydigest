"""
Sends the raw event list to Claude to filter for toddler-appropriateness,
rank by quality, and write short parent-friendly blurbs.
"""
import json
import os

import anthropic

MODEL = "claude-sonnet-4-6"


def build_prompt(events, config):
    age_range = config.get("child_age_range", "toddler")
    max_events = config.get("max_events", 8)

    return f"""You are helping a parent find weekend events suitable for a
child aged {age_range}, in or near {config['location']['city']}, {config['location']['state']}.

Below is a raw list of candidate events pulled from public event feeds. Many
will be irrelevant (concerts, bar events, adults-only, sports games with no
kids programming, etc). Your job:

1. Filter to only events realistically enjoyable/appropriate for a {age_range}.
2. Rank the remaining events by likely quality (novelty, hands-on/interactive,
   short/flexible time commitment, weather contingency if outdoor).
3. Return at most {max_events} events.
4. For each, write a 1-2 sentence parent-facing blurb: what it is, why it
   suits a toddler, and any practical note (stroller-friendly, timed entry,
   free/paid).

Respond ONLY with valid JSON, no other text, in this shape:
{{
  "events": [
    {{
      "title": "...",
      "date": "...",
      "time": "...",
      "venue": "...",
      "url": "...",
      "blurb": "..."
    }}
  ]
}}

Raw events:
{json.dumps(events, indent=2)}
"""


def score(events, config):
    if not events:
        return []

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": build_prompt(events, config)}],
    )

    text = message.content[0].text.strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(text)
        return parsed.get("events", [])
    except json.JSONDecodeError:
        print("Could not parse Claude's response as JSON:")
        print(text)
        return []
