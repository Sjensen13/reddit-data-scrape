import os
import time
import csv
import praw

SUBREDDIT = "Steam"
MODE = "new"
LIMIT = 1000
OUTPUT_CSV = "reddit_posts.csv"

FLAIR_WHITELIST = set()  # e.g. {"Review", "Bug Report"} ; empty = no filter

# --------- AUTH ----------
# Best practice: set these as environment variables
# export REDDIT_CLIENT_ID="..."
# export REDDIT_CLIENT_SECRET="..."
# export REDDIT_USER_AGENT="myapp:reddit_scraper:v1 (by u/yourusername)"


def build_reddit_client():
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")

    missing = []
    if not client_id:
        missing.append("REDDIT_CLIENT_ID")
    if not client_secret:
        missing.append("REDDIT_CLIENT_SECRET")
    if not user_agent:
        missing.append("REDDIT_USER_AGENT")

    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(
            "Missing Reddit credentials. Set environment variables: "
            f"{missing_list}"
        )

    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )


def get_posts(reddit_client, subreddit_name: str, mode: str, limit: int):
    sub = reddit_client.subreddit(subreddit_name)

    if mode == "new":
        return sub.new(limit=limit)
    if mode == "hot":
        return sub.hot(limit=limit)
    if mode == "top":
        return sub.top(limit=limit)

    raise ValueError("MODE must be one of: new, hot, top")


def safe_text(s):
    return "" if s is None else str(s)


def main():
    reddit = build_reddit_client()
    fieldnames = [
        "post_id",
        "created_utc",
        "title",
        "body",
        "score",
        "num_comments",
        "flair",
    ]

    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        count = 0
        for post in get_posts(reddit, SUBREDDIT, MODE, LIMIT):
            flair = safe_text(post.link_flair_text)

            if FLAIR_WHITELIST and flair not in FLAIR_WHITELIST:
                continue

            row = {
                "post_id": post.id,  # unique identifier
                "created_utc": int(post.created_utc),
                "title": safe_text(post.title),
                "body": safe_text(post.selftext),  # main text
                "score": int(post.score),
                "num_comments": int(post.num_comments),
                "flair": flair,
            }
            writer.writerow(row)
            count += 1

            # tiny pause is polite and reduces rate-limit issues
            time.sleep(0.05)

    print(f"Saved {count} posts to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
