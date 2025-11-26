import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter


@st.cache_data
def load_data():
    with open("test.json", "r", encoding="utf-8") as file:
        return json.load(file)


st.set_page_config(page_title="Facebook Post Analytics", layout="wide", page_icon="📊")

st.markdown(
    """
    <style>
    .main-header {
        font-size: 36px;
        font-weight: bold;
        color: #1877f2;
        text-align: center;
        margin-bottom: 30px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .post-content {
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e1e8ed;
        margin-bottom: 20px;
    }
    </style>
""",
    unsafe_allow_html=True,
)


data = load_data()

st.markdown(
    '<div class="main-header">📊 Facebook Post Analytics Dashboard</div>',
    unsafe_allow_html=True,
)

st.sidebar.title("📋 Navigation")
section = st.sidebar.radio(
    "Go to",
    [
        "Overview",
        "Post Details",
        "Comments Analysis",
        "Sentiment & Emotion",
        "Engagement Metrics",
    ],
)

post_content = data["post"]["content"]
post_url = data["post"]["url"]
post_date = data["post"]["raw_data"].get("date_posted", "N/A")
comments = data["comments"]
stats = data["statistics"]

photo_url = None
if data["post"]["raw_data"].get("attachments"):
    photo_url = data["post"]["raw_data"]["attachments"][0]["url"]

likes_breakdown = data["post"]["raw_data"].get("num_likes_type", [])
total_likes = sum([item["num"] for item in likes_breakdown])
num_comments = data["post"]["raw_data"].get("num_comments", 0)
num_shares = data["post"]["raw_data"].get("num_shares", 0)

# ============ OVERVIEW SECTION ============
if section == "Overview":
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👍 Total Reactions", total_likes)
    with col2:
        st.metric("💬 Comments", num_comments)
    with col3:
        st.metric("🔄 Shares", num_shares)
    with col4:
        engagement_rate = total_likes + num_comments + num_shares
        st.metric("📈 Total Engagement", engagement_rate)

    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Post Content")
        st.markdown(
            f'<div class="post-content">{post_content}</div>', unsafe_allow_html=True
        )
        st.markdown(f"🔗 [View Original Post]({post_url})")
        st.caption(f"📅 Posted: {post_date}")

    with col2:
        st.subheader("📷 Attachment")
        if photo_url:
            st.image(photo_url, use_container_width=True, caption="Post Image")
        else:
            st.info("No image attachment available")

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("❤️ Reactions Breakdown")
        if likes_breakdown:
            reaction_df = pd.DataFrame(likes_breakdown)
            # Add emojis to reaction types
            emoji_map = {
                "Like": "👍 Like",
                "Love": "❤️ Love",
                "Haha": "😂 Haha",
                "Wow": "😮 Wow",
                "Sad": "😢 Sad",
                "Angry": "😠 Angry",
            }
            reaction_df["type_emoji"] = (
                reaction_df["type"].map(emoji_map).fillna(reaction_df["type"])
            )
            fig = px.pie(
                reaction_df,
                values="num",
                names="type_emoji",
                title="Reaction Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("💭 Comment Sentiments")
        sentiment_counts = Counter(
            [c["sentiment"] for c in comments if c.get("sentiment")]
        )
        sentiment_df = pd.DataFrame(
            sentiment_counts.items(), columns=["Sentiment", "Count"]
        )
        fig = px.bar(
            sentiment_df,
            x="Sentiment",
            y="Count",
            color="Sentiment",
            color_discrete_map={
                "Positive": "#28a745",
                "Negative": "#dc3545",
                "Neutral": "#6c757d",
            },
            title="Sentiment Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

# ============ POST DETAILS SECTION ============
elif section == "Post Details":
    st.header("📄 Detailed Post Information")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 Full Content")
        st.markdown(
            f'<div class="post-content">{post_content}</div>', unsafe_allow_html=True
        )

        st.subheader("📊 Post Metadata")
        metadata = {
            "Post URL": post_url,
            "Date Posted": post_date,
            "Author": data["post"]["raw_data"].get("user_username_raw", "N/A"),
            "Profile Handle": data["post"]["raw_data"].get("profile_handle", "N/A"),
            "Post ID": data["post"]["raw_data"].get("post_id", "N/A"),
            "Verified": (
                "✅ Yes"
                if data["post"]["raw_data"].get("page_is_verified")
                else "❌ No"
            ),
            "Followers": data["post"]["raw_data"].get("page_followers", "N/A"),
        }
        for key, value in metadata.items():
            st.text(f"{key}: {value}")

    with col2:
        st.subheader("📷 Post Image")
        if photo_url:
            st.image(photo_url, use_container_width=True)

        st.subheader("🎯 Engagement Summary")
        st.metric("Total Reactions", total_likes, delta=None)
        st.metric("Comments", num_comments, delta=None)
        st.metric("Shares", num_shares, delta=None)

    st.markdown("---")

    st.subheader("❤️ Detailed Reactions")
    if likes_breakdown:
        reaction_df = pd.DataFrame(likes_breakdown)
        reaction_df["Percentage"] = (reaction_df["num"] / total_likes * 100).round(2)
        emoji_map = {
            "Like": "👍",
            "Love": "❤️",
            "Haha": "😂",
            "Wow": "😮",
            "Sad": "😢",
            "Angry": "😠",
        }
        reaction_df["Emoji"] = reaction_df["type"].map(emoji_map).fillna("")
        reaction_df_display = reaction_df[["Emoji", "type", "num", "Percentage"]]
        reaction_df_display.columns = ["", "Type", "Count", "Percentage"]

        col1, col2 = st.columns([1, 1])
        with col1:
            st.dataframe(reaction_df_display, use_container_width=True)
        with col2:
            reaction_df["type_emoji"] = reaction_df["type"].apply(
                lambda x: f"{emoji_map.get(x, '')} {x}"
            )
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=reaction_df["type_emoji"],
                        y=reaction_df["num"],
                        text=reaction_df["num"],
                        textposition="auto",
                        marker_color=[
                            "#1877f2",
                            "#f44336",
                            "#e91e63",
                            "#ff9800",
                            "#9c27b0",
                        ],
                    )
                ]
            )
            fig.update_layout(
                title="Reactions Count",
                xaxis_title="Reaction Type",
                yaxis_title="Count",
            )
            st.plotly_chart(fig, use_container_width=True)

# ============ COMMENTS ANALYSIS SECTION ============
elif section == "Comments Analysis":
    st.header("💬 Comments Analysis")

    st.metric("Total Comments Analyzed", len(comments))

    st.markdown("---")

    st.subheader("📋 All Comments")

    comments_data = []
    for comment in comments:
        comments_data.append(
            {
                "User": comment.get("user_name", "Unknown"),
                "Comment": comment.get("comment_text", ""),
                "Date": comment.get("date_created", "N/A"),
                "Likes": comment.get("likes_count", 0),
                "Replies": comment.get("replies_count", 0),
                "Sentiment": comment.get("sentiment", "N/A"),
                "Emotion": comment.get("emotion", "N/A"),
                "Confidence": f"{comment.get('confidence', 0):.2f}",
            }
        )

    comments_df = pd.DataFrame(comments_data)
    st.dataframe(comments_df, use_container_width=True, height=400)

    st.markdown("---")

    st.subheader("📏 Comment Length Distribution")
    comments_df["Length"] = comments_df["Comment"].str.len()
    fig = px.histogram(
        comments_df,
        x="Length",
        nbins=20,
        title="Distribution of Comment Lengths",
        labels={"Length": "Characters", "count": "Number of Comments"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("⏰ Comments Timeline")
    comments_df["DateTime"] = pd.to_datetime(comments_df["Date"])
    comments_df["Hour"] = comments_df["DateTime"].dt.hour
    hourly_counts = comments_df["Hour"].value_counts().sort_index()

    fig = px.line(
        x=hourly_counts.index,
        y=hourly_counts.values,
        title="Comments Over Time (by Hour)",
        labels={"x": "Hour of Day", "y": "Number of Comments"},
    )
    st.plotly_chart(fig, use_container_width=True)

# ============ SENTIMENT & EMOTION SECTION ============
elif section == "Sentiment & Emotion":
    st.header("🎭 Sentiment & Emotion Analysis")

    col1, col2, col3 = st.columns(3)

    sentiment_counts = Counter([c["sentiment"] for c in comments if c.get("sentiment")])
    with col1:
        st.metric("😊 Positive", sentiment_counts.get("Positive", 0))
    with col2:
        st.metric("😐 Neutral", sentiment_counts.get("Neutral", 0))
    with col3:
        st.metric("😞 Negative", sentiment_counts.get("Negative", 0))

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Sentiment Distribution")
        sentiment_df = pd.DataFrame(
            sentiment_counts.items(), columns=["Sentiment", "Count"]
        )
        sentiment_emoji_map = {
            "Positive": "😊 Positive",
            "Negative": "😞 Negative",
            "Neutral": "😐 Neutral",
        }
        sentiment_df["Sentiment_emoji"] = sentiment_df["Sentiment"].map(
            sentiment_emoji_map
        )
        fig = px.pie(
            sentiment_df,
            values="Count",
            names="Sentiment_emoji",
            color="Sentiment",
            color_discrete_map={
                "Positive": "#28a745",
                "Negative": "#dc3545",
                "Neutral": "#6c757d",
            },
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎭 Emotion Distribution")
        emotion_counts = Counter([c["emotion"] for c in comments if c.get("emotion")])
        emotion_df = pd.DataFrame(emotion_counts.items(), columns=["Emotion", "Count"])
        emotion_emoji_map = {
            "Joy": "😄 Joy",
            "Anger": "😠 Anger",
            "Fear": "😨 Fear",
            "Sadness": "😢 Sadness",
            "Surprise": "😲 Surprise",
            "Neutral": "😐 Neutral",
        }
        emotion_df["Emotion_emoji"] = (
            emotion_df["Emotion"].map(emotion_emoji_map).fillna(emotion_df["Emotion"])
        )
        fig = px.pie(
            emotion_df,
            values="Count",
            names="Emotion_emoji",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("🔍 Sentiment vs Emotion Heatmap")
    sentiment_emotion_data = []
    for comment in comments:
        if comment.get("sentiment") and comment.get("emotion"):
            sentiment_emotion_data.append(
                {"Sentiment": comment["sentiment"], "Emotion": comment["emotion"]}
            )

    if sentiment_emotion_data:
        se_df = pd.DataFrame(sentiment_emotion_data)
        heatmap_data = pd.crosstab(se_df["Sentiment"], se_df["Emotion"])

        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Emotion", y="Sentiment", color="Count"),
            title="Sentiment-Emotion Correlation",
            color_continuous_scale="RdYlGn_r",
            text_auto=True,
        )
        fig.update_traces(textfont_size=16, textfont_color="black", texttemplate="%{z}")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("📈 Confidence Score Distribution")
    confidence_scores = [c["confidence"] for c in comments if c.get("confidence")]
    if confidence_scores:
        fig = px.histogram(
            confidence_scores,
            nbins=20,
            title="Distribution of ML Confidence Scores",
            labels={"value": "Confidence Score", "count": "Number of Comments"},
        )
        st.plotly_chart(fig, use_container_width=True)

        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        st.info(f"Average Confidence Score: {avg_confidence:.2%}")

# ============ ENGAGEMENT METRICS SECTION ============
elif section == "Engagement Metrics":
    st.header("📈 Engagement Metrics")

    total_reactions = total_likes
    total_comments_count = num_comments
    total_shares_count = num_shares
    total_engagement = total_reactions + total_comments_count + total_shares_count

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("👍 Total Reactions", total_reactions)
    with col2:
        st.metric("💬 Total Comments", total_comments_count)
    with col3:
        st.metric("🔄 Total Shares", total_shares_count)
    with col4:
        st.metric("🎯 Total Engagement", total_engagement)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Engagement Breakdown")
        engagement_data = pd.DataFrame(
            {
                "Type": ["Reactions", "Comments", "Shares"],
                "Count": [total_reactions, total_comments_count, total_shares_count],
            }
        )

        fig = px.bar(
            engagement_data,
            x="Type",
            y="Count",
            color="Type",
            title="Engagement by Type",
            text="Count",
        )
        fig.update_traces(texttemplate="%{text}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🥧 Engagement Ratio")
        fig = px.pie(
            engagement_data,
            values="Count",
            names="Type",
            title="Engagement Distribution",
            hole=0.4,
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    st.subheader("❤️ Reaction Types Performance")
    if likes_breakdown:
        reaction_df = pd.DataFrame(likes_breakdown)

        col1, col2 = st.columns([2, 1])

        with col1:
            emoji_map = {
                "Like": "👍",
                "Love": "❤️",
                "Haha": "😂",
                "Wow": "😮",
                "Sad": "😢",
                "Angry": "😠",
            }
            reaction_df["type_emoji"] = reaction_df["type"].apply(
                lambda x: f"{emoji_map.get(x, '')} {x}"
            )
            fig = go.Figure(
                data=[
                    go.Bar(
                        name="Count",
                        x=reaction_df["type_emoji"],
                        y=reaction_df["num"],
                        text=reaction_df["num"],
                        textposition="auto",
                        marker_color=[
                            "#1877f2",
                            "#ff6b6b",
                            "#ff69b4",
                            "#ffd700",
                            "#ff4500",
                        ],
                    )
                ]
            )
            fig.update_layout(
                title="Reactions by Type", xaxis_title="Reaction", yaxis_title="Count"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.write("### Reaction Stats")
            for reaction in likes_breakdown:
                percentage = reaction["num"] / total_likes * 100
                emoji = emoji_map.get(reaction["type"], "")
                st.metric(
                    label=f"{emoji} {reaction['type']}",
                    value=reaction["num"],
                    delta=f"{percentage:.1f}%",
                )

    st.subheader("💬 Comment Engagement Details")
    comments_with_likes = [c for c in comments if c.get("likes_count", 0) > 0]
    comments_with_replies = [c for c in comments if c.get("replies_count", 0) > 0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Comments with Likes", len(comments_with_likes))
    with col2:
        st.metric("Comments with Replies", len(comments_with_replies))
    with col3:
        avg_comment_length = (
            sum([len(c.get("comment_text", "")) for c in comments]) / len(comments)
            if comments
            else 0
        )
        st.metric("Avg Comment Length", f"{avg_comment_length:.0f} chars")

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888; padding: 20px;'>
        <p>📊 Facebook Post Analytics Dashboard | Data scraped on {}</p>
    </div>
""".format(
        data.get("scraped_at", "N/A")
    ),
    unsafe_allow_html=True,
)
