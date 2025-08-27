import praw
import re
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

class RedditTranscriptService:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
            check_for_async=False
        )
    
    def extract_submission_id(self, reddit_url: str) -> Optional[str]:
        """Extract submission ID from Reddit URL"""
        match = re.search(r'/comments/([a-zA-Z0-9]+)', reddit_url)
        return match.group(1) if match else None
    
    def get_transcript(self, reddit_url: str) -> Optional[Dict]:
        """Get complete Reddit transcript from URL"""
        try:
            # Extract submission ID
            submission_id = self.extract_submission_id(reddit_url)
            if not submission_id:
                return None
            
            # Get submission
            submission = self.reddit.submission(id=submission_id)
            
            # Get only top-level comments (no nested replies) - top 25 by upvotes
            submission.comments.replace_more(limit=0)  # Don't expand replies to avoid nested comments
            top_level_comments = []
            
            # Collect only top-level comments (direct replies to the post)
            for comment in submission.comments:
                if hasattr(comment, 'body') and comment.body != '[deleted]' and comment.body != '[removed]':
                    top_level_comments.append({
                        'id': comment.id,
                        'text': comment.body,
                        'score': comment.score,
                        'created_utc': comment.created_utc
                    })
            
            # Sort by score (upvotes) in descending order and take top 25
            top_level_comments.sort(key=lambda x: x['score'], reverse=True)
            all_comments = top_level_comments[:25]
            
            # Build transcript response
            transcript = {
                'success': True,
                'reddit_url': reddit_url,
                'post': {
                    'title': submission.title,
                    'selftext': submission.selftext if submission.selftext else '',
                    'score': submission.score,
                    'created_utc': submission.created_utc
                },
                'comments': all_comments,
                'total_comments': len(all_comments)
            }
            
            return transcript
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'reddit_url': reddit_url
            }

# Example usage and testing
if __name__ == "__main__":
    service = RedditTranscriptService()
    
    # Test with a sample URL
    test_url = "https://reddit.com/r/bayarea/comments/example/best_viewpoints"
    
    print("Testing Reddit Transcript Service...")
    print("=" * 50)
    
    try:
        transcript = service.get_transcript(test_url)
        if transcript and transcript.get('success'):
            print(f"✅ Successfully extracted transcript")
            print(f"Post title: {transcript['post']['title']}")
            print(f"Total comments: {transcript['total_comments']}")
            print(f"Sample comment: {transcript['comments'][0]['text'][:100] if transcript['comments'] else 'No comments'}")
        else:
            print(f"❌ Failed to extract transcript: {transcript.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Note: Provide a real Reddit URL for testing")