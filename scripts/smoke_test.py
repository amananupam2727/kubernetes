import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def check(base_url, path, validate):
    url = base_url.rstrip("/") + path

    try:
        with urlopen(url, timeout=10) as response:
            if response.status != 200:
                raise ValueError(f"Expected HTTP 200, got {response.status}")
            data = json.load(response)

        if not validate(data):
            raise ValueError("Unexpected response structure or values")

        print(f"PASS {path}")
        return True

    except (HTTPError, URLError, OSError, ValueError) as error:
        print(f"FAIL {path}: {error}")
        return False


def valid_tasks(data):
    return isinstance(data, list) and all(
        isinstance(task, dict)
        and type(task.get("id")) is int
        and isinstance(task.get("title"), str)
        and type(task.get("completed")) is bool
        for task in data
    )


def main():
    parser = argparse.ArgumentParser(description="Check task tracker health")
    parser.add_argument("--url", default="http://127.0.0.1:8080")
    args = parser.parse_args()

    checks = [
        ("/healthz", lambda data: data == {"status": "alive"}),
        ("/readyz", lambda data: data == {"status": "ready"}),
        ("/api/tasks", valid_tasks),
    ]

    results = [
        check(args.url, path, validate)
        for path, validate in checks
    ]

    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
