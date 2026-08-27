import sys
import yaml

from fetch_events import fetch_all
from score_events import score
from send_digest import send


def load_config():
    try:
        with open("config.yaml") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("config.yaml not found. Copy config.example.yaml to config.yaml and fill it in.")
        sys.exit(1)


def main():
    config = load_config()

    print("Fetching candidate events...")
    raw_events = fetch_all(config)
    print(f"Found {len(raw_events)} raw candidates.")

    print("Scoring/filtering with Claude...")
    curated = score(raw_events, config)
    print(f"{len(curated)} events made the digest.")

    print("Sending email digest...")
    send(curated, config)


if __name__ == "__main__":
    main()
