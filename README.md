# Facebook Post Scraper & Sentiment Analyzer

A command-line tool to scrape Facebook posts and comments with AI-powered sentiment analysis.

## Prerequisites

- Python 3.11+
- BrightData API account with dataset access
- OpenRouter API key (for sentiment analysis)

## Installation

1. Install required packages:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API credentials:

```env
BRIGHTDATA_API_KEY=your_brightdata_api_key
POST_DATASET_ID=your_post_dataset_id
COMMENTS_DATASET_ID=your_comments_dataset_id
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Usage

### Basic Usage

Scrape a post with up to 100 comments:

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123456789"
```

### Custom Comment Limit

Scrape specific number of comments:

```bash
python facebook_cli.py "https://m.facebook.com/story.php?story_fbid=123&id=456" -n 50
```

### Custom Output File

Save to a specific file:

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123" -o my_data.json
```

### Post Only

Scrape only the post without comments:

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123" --post-only
```

### Comments Only

Scrape only comments without post details:

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123" --comments-only
```

### Skip Sentiment Analysis

Faster scraping without AI analysis:

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123" --no-sentiment
```

## Command-Line Options

| Option               | Description                          | Default                        |
| -------------------- | ------------------------------------ | ------------------------------ |
| `url`                | Facebook post URL (required)         | -                              |
| `-n, --num-comments` | Maximum number of comments to scrape | 100                            |
| `-o, --output`       | Output JSON file name                | `facebook_data_TIMESTAMP.json` |
| `--post-only`        | Scrape only the post, skip comments  | False                          |
| `--comments-only`    | Scrape only comments, skip post      | False                          |
| `--no-sentiment`     | Skip sentiment analysis (faster)     | False                          |

## Output Format

The tool generates a JSON file with the following structure:

```json
{
  "scraped_at": "2025-11-26 21:17:49",
  "post_url": "https://m.facebook.com/story.php?story_fbid=123&id=456",
  "post": {
    "content": "Post text...",
    "author": "Author Name",
    "date": "2025-11-26T08:34:35.000Z",
    "likes": 206,
    "shares": 4,
    "comments_count": 41,
    "url": "...",
    "raw_data": { ... }
  },
  "comments": [
    {
      "user_name": "User Name",
      "user_url": "https://www.facebook.com/username",
      "date_created": "2025-11-26T08:41:40.000Z",
      "comment_text": "Comment text...",
      "likes_count": 5,
      "replies_count": 2,
      "sentiment": "Positive",
      "emotion": "Joy",
      "confidence": 0.85
    }
  ],
  "statistics": {
    "total_comments_scraped": 16,
    "post_likes": 206,
    "post_shares": 4
  }
}
```

## Sentiment Analysis

The tool uses Google Gemini 2.5 Flash via OpenRouter to analyze:

- **Sentiment**: Positive, Negative, or Neutral
- **Emotion**: Joy, Anger, Sadness, Fear, Surprise, or Neutral
- **Confidence**: 0.0 to 1.0 score indicating analysis certainty

## Examples

**Scrape trending post with 200 comments:**

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123" -n 200
```

**Quick scrape without AI (faster):**

```bash
python facebook_cli.py "https://m.facebook.com/story.php?story_fbid=123&id=456" -n 50 --no-sentiment
```

**Custom output location:**

```bash
python facebook_cli.py "https://www.facebook.com/page/posts/123" -o ./data/analysis_2025.json
```

## Notes

- The tool automatically converts desktop URLs to mobile URLs for better scraping
- Scraping progress is displayed in real-time
- Sentiment analysis processes comments in batches with progress updates
- All timestamps are in ISO 8601 format (UTC)
