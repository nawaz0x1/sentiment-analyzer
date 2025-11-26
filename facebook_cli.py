import os
import requests
import time
import json
import argparse
import load_dotenv
from datetime import datetime
from openai import OpenAI


load_dotenv.load_dotenv()

BRIGHTDATA_API_KEY = os.getenv("BRIGHTDATA_API_KEY")
POST_DATASET_ID = os.getenv("POST_DATASET_ID")
COMMENTS_DATASET_ID = os.getenv("COMMENTS_DATASET_ID")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize OpenRouter client
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def trigger_brightdata_scrape(url, dataset_id, limit_records=None):
    """Trigger a BrightData scraping job"""
    trigger_url = "https://api.brightdata.com/datasets/v3/trigger"
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
        "Content-Type": "application/json",
    }
    params = {
        "dataset_id": dataset_id,
        "include_errors": "true",
    }

    data = [{"url": url}]
    if limit_records:
        data[0]["limit_records"] = limit_records

    response = requests.post(trigger_url, headers=headers, params=params, json=data)

    if response.status_code == 200:
        return response.json().get("snapshot_id")
    else:
        print(f"Error triggering scrape: {response.text}")
        return None


def check_scrape_progress(snapshot_id):
    """Check the progress of a BrightData scraping job"""
    url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json().get("status")
    else:
        return None


def get_scrape_results(snapshot_id):
    """Get the results of a completed BrightData scraping job"""
    url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
    headers = {
        "Authorization": f"Bearer {BRIGHTDATA_API_KEY}",
    }
    params = {
        "format": "json",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting results: {response.text}")
        return None


def analyze_sentiment(post_content, comment_text):
    """
    Analyze sentiment of a comment using OpenRouter LLM

    Args:
        post_content: The original post text
        comment_text: The comment text to analyze

    Returns:
        dict: Sentiment analysis with sentiment, emotion, and confidence
    """
    try:
        prompt = f"""Analyze the sentiment and emotion of this user comment in response to the post.

POST:
{post_content}

USER COMMENT:
{comment_text}

Respond ONLY with a JSON object in this exact format:
{{
  "sentiment": "Positive" or "Negative" or "Neutral",
  "emotion": "Joy" or "Anger" or "Sadness" or "Fear" or "Surprise" or "Neutral",
  "confidence": 0.0 to 1.0
}}"""

        completion = client.chat.completions.create(
            extra_headers={
                "HTTP-Referer": "https://facebook-scraper",
                "X-Title": "Facebook Sentiment Analyzer",
            },
            model="google/gemini-2.5-flash",
            messages=[{"role": "user", "content": prompt}],
        )

        result = completion.choices[0].message.content

        # Try to parse JSON response
        try:
            # Extract JSON if wrapped in markdown code blocks
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0].strip()
            elif "```" in result:
                result = result.split("```")[1].split("```")[0].strip()

            sentiment_data = json.loads(result)
            return sentiment_data
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {"sentiment": "Neutral", "emotion": "Neutral", "confidence": 0.5}

    except Exception as e:
        print(f"    Sentiment analysis error: {e}")
        return {"sentiment": "Neutral", "emotion": "Neutral", "confidence": 0.0}


def scrape_facebook_post(post_url):
    """Scrape a Facebook post content"""
    print("🔄 Scraping post...")

    # Trigger the scrape
    snapshot_id = trigger_brightdata_scrape(post_url, POST_DATASET_ID)

    if not snapshot_id:
        return None

    print(f"   Snapshot ID: {snapshot_id}")

    # Wait for completion
    while True:
        status = check_scrape_progress(snapshot_id)

        if status == "ready":
            print("   ✓ Post scraping complete!")
            break
        elif status == "failed":
            print("   ✗ Post scraping failed")
            return None

        print(f"   Status: {status}...")
        time.sleep(5)

    # Get results
    results = get_scrape_results(snapshot_id)

    if results and len(results) > 0:
        post = results[0]
        return {
            "content": post.get("content", ""),
            "author": post.get("user_name", ""),
            "date": post.get("date_created", ""),
            "likes": post.get("likes_count", 0),
            "shares": post.get("shares_count", 0),
            "comments_count": post.get("comments_count", 0),
            "url": post_url,
            "raw_data": post,
        }

    return None


def scrape_facebook_comments(
    post_url, limit_records=100, post_content="", analyze=True
):
    """Scrape comments from a Facebook post"""
    print(f"🔄 Scraping comments (limit: {limit_records})...")

    # Trigger the scrape
    snapshot_id = trigger_brightdata_scrape(
        post_url, COMMENTS_DATASET_ID, limit_records
    )

    if not snapshot_id:
        return None

    print(f"   Snapshot ID: {snapshot_id}")

    # Wait for completion
    while True:
        status = check_scrape_progress(snapshot_id)

        if status == "ready":
            print("   ✓ Comments scraping complete!")
            break
        elif status == "failed":
            print("   ✗ Comments scraping failed")
            return None

        print(f"   Status: {status}...")
        time.sleep(5)

    # Get results
    results = get_scrape_results(snapshot_id)

    if results:
        comments_list = []
        total = len(results)

        if analyze:
            print(f"\n Analyzing sentiment for {total} comments...")

        for idx, comment in enumerate(results, 1):
            comment_text = comment.get("comment_text", "")

            # Analyze sentiment if enabled and comment has text
            if analyze and comment_text and post_content:
                if idx % 10 == 0 or idx == total:
                    print(f"   Analyzing... {idx}/{total}")
                sentiment_data = analyze_sentiment(post_content, comment_text)
            else:
                sentiment_data = {
                    "sentiment": "Neutral",
                    "emotion": "Neutral",
                    "confidence": 0.0,
                }

            comment_data = {
                "user_name": comment.get("user_name", "Unknown"),
                "user_url": comment.get("user_url", ""),
                "date_created": comment.get("date_created", ""),
                "comment_text": comment_text,
                "likes_count": comment.get("likes_count", 0),
                "replies_count": comment.get("replies_count", 0),
                "sentiment": sentiment_data.get("sentiment", "Neutral"),
                "emotion": sentiment_data.get("emotion", "Neutral"),
                "confidence": sentiment_data.get("confidence", 0.0),
            }
            comments_list.append(comment_data)

        if analyze:
            print("   ✓ Sentiment analysis complete!")

        return comments_list

    return []


def save_to_json(data, filename):
    """Save data to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f" Saved to: {filename}")


def display_summary(post_data, comments_data):
    """Display a summary of scraped data"""
    print("\n" + "=" * 60)
    print(" SCRAPING SUMMARY")
    print("=" * 60)

    if post_data:
        print(f"\n POST:")
        print(f"   Author: {post_data.get('author', 'N/A')}")
        print(f"   Date: {post_data.get('date', 'N/A')}")
        print(f"   Likes: {post_data.get('likes', 0)}")
        print(f"   Shares: {post_data.get('shares', 0)}")
        print(f"   Comments: {post_data.get('comments_count', 0)}")
        print(f"   Sentiment: {post_data.get('sentiment', 'N/A')}")
        print(f"   Content: {post_data.get('content', '')[:100]}...")

    if comments_data:
        print(f"\n COMMENTS: {len(comments_data)} scraped")

        # Show first 5 comments
        for i, comment in enumerate(comments_data[:5], 1):
            print(f"\n   Comment {i}:")
            print(f"   User: {comment.get('user_name', 'Unknown')}")
            print(f"   Date: {comment.get('date_created', 'N/A')}")
            print(f"   Likes: {comment.get('likes_count', 0)}")
            print(f"   Sentiment: {comment.get('sentiment', 'N/A')}")
            print(f"   Text: {comment.get('comment_text', '')[:80]}...")

        if len(comments_data) > 5:
            print(f"\n   ... and {len(comments_data) - 5} more comments")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Facebook Post & Comments Scraper with Sentiment Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python facebook_cli.py "https://www.facebook.com/page/posts/123456789"
  python facebook_cli.py "https://m.facebook.com/story.php?story_fbid=123&id=456" -n 50
  python facebook_cli.py "https://www.facebook.com/page/posts/123" -n 200 -o my_data.json
        """,
    )

    parser.add_argument("url", help="Facebook post URL to scrape")

    parser.add_argument(
        "-n",
        "--num-comments",
        type=int,
        default=100,
        help="Maximum number of comments to scrape (default: 100)",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output JSON file name (default: facebook_data_TIMESTAMP.json)",
    )

    parser.add_argument(
        "--post-only", action="store_true", help="Scrape only the post, skip comments"
    )

    parser.add_argument(
        "--comments-only", action="store_true", help="Scrape only comments, skip post"
    )

    parser.add_argument(
        "--no-sentiment",
        action="store_true",
        help="Skip sentiment analysis (faster)",
    )

    args = parser.parse_args()

    # Convert to mobile URL if needed
    post_url = args.url
    if "www.facebook.com" in post_url:
        post_url = post_url.replace("www.facebook.com", "m.facebook.com")
        print(f"🔄 Converted to mobile URL: {post_url}")

    print("\n" + "=" * 60)
    print(" FACEBOOK SCRAPER")
    print("=" * 60)
    print(f"URL: {post_url}")
    print(f"Max Comments: {args.num_comments}")
    print("=" * 60 + "\n")

    post_data = None
    comments_data = []

    try:
        # Scrape post
        if not args.comments_only:
            post_data = scrape_facebook_post(post_url)
            if not post_data:
                print(" Failed to scrape post")
                return

        # Scrape comments
        if not args.post_only:
            post_content = post_data.get("content", "") if post_data else ""
            analyze = not args.no_sentiment
            comments_data = scrape_facebook_comments(
                post_url, args.num_comments, post_content=post_content, analyze=analyze
            )
            if comments_data is None:
                print(" Failed to scrape comments")
                return

        # Display summary
        display_summary(post_data, comments_data)

        # Prepare output data
        output_data = {
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "post_url": post_url,
            "post": post_data,
            "comments": comments_data,
            "statistics": {
                "total_comments_scraped": len(comments_data),
                "post_likes": post_data.get("likes", 0) if post_data else 0,
                "post_shares": post_data.get("shares", 0) if post_data else 0,
            },
        }

        # Save to file
        if args.output:
            output_file = args.output
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"facebook_data_{timestamp}.json"

        save_to_json(output_data, output_file)

        print(f"\nScraping completed successfully!")
        print(f" Data saved to: {output_file}")

    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
