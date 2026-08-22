"""Create a post and publish it.

Point it at a local dev API:

    export FOPOST_API_KEY=fp_...
    export FOPOST_BASE_URL=http://localhost:8080/api/v1
    python examples/create_post.py "Hello from the Python SDK"

Without --publish it stops at a draft, so you can run it against a real
workspace without anything going out.
"""

from __future__ import annotations

import argparse
import os
import sys

from fopost import DEFAULT_BASE_URL, Fopost, FopostError


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a post with the FoPost SDK.")
    parser.add_argument(
        "text",
        nargs="?",
        default="Hello from the FoPost Python SDK",
        help="post body",
    )
    parser.add_argument("--workspace", help="workspace id (defaults to the first one)")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="publish immediately instead of leaving a draft",
    )
    args = parser.parse_args()

    api_key = os.environ.get("FOPOST_API_KEY")
    if not api_key:
        print("Set FOPOST_API_KEY first.", file=sys.stderr)
        return 1

    base_url = os.environ.get("FOPOST_BASE_URL", DEFAULT_BASE_URL)

    with Fopost(api_key=api_key, base_url=base_url) as client:
        try:
            workspace_id = args.workspace
            if not workspace_id:
                workspaces = client.workspaces.list()
                if not workspaces:
                    print("No workspaces on this key.", file=sys.stderr)
                    return 1
                workspace_id = workspaces[0].id
                print(f"Workspace: {workspaces[0].name} ({workspace_id})")

            accounts = client.accounts.list(workspace_id=workspace_id)
            if not accounts:
                print("No connected accounts in this workspace.", file=sys.stderr)
                return 1
            for account in accounts:
                print(f"  · {account.platform}: @{account.username}")

            post = client.posts.create(
                workspace_id=workspace_id,
                content=args.text,
                accounts=[a.id for a in accounts],
            )
            print(f"Created post {post.id} ({post.status})")

            if args.publish:
                client.posts.publish(post.id)
                for delivery in client.posts.deliveries(post.id):
                    print(f"  · {delivery.platform}: {delivery.status}")

            return 0

        except FopostError as err:
            print(f"API error: {err}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
