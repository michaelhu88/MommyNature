import praw
import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from googlesearch import search
import os
from dotenv import load_dotenv
import time

load_dotenv()

class RedditScraper:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
            check_for_async=False
        )
    
    def search_reddit_via_google(self, query: str, max_results: int = 5) -> List[str]:
        """Search for Reddit posts using Google search"""
        search_query = f"{query} site:reddit.com"
        reddit_urls = []
        
        try:
            for url in search(search_query, num_results=max_results):
                if 'reddit.com' in url and '/comments/' in url:
                    reddit_urls.append(url)
                    if len(reddit_urls) >= max_results:
                        break
        except Exception as e:
            print(f"Error searching Google: {e}")
        
        return reddit_urls
    
    def extract_submission_id(self, reddit_url: str) -> Optional[str]:
        """Extract submission ID from Reddit URL"""
        match = re.search(r'/comments/([a-zA-Z0-9]+)', reddit_url)
        return match.group(1) if match else None
    
    def get_submission_with_comments(self, submission_id: str) -> Optional[Dict]:
        """Get Reddit submission with top comments"""
        try:
            submission = self.reddit.submission(id=submission_id)
            
            # Add delay to avoid rate limiting
            time.sleep(1)
            
            # Get top comments
            submission.comments.replace_more(limit=0)
            top_comments = []
            
            for comment in submission.comments[:10]:  # Top 10 comments
                if hasattr(comment, 'body') and len(comment.body) > 20:
                    top_comments.append({
                        'body': comment.body,
                        'score': comment.score,
                        'author': str(comment.author) if comment.author else '[deleted]'
                    })
            
            return {
                'title': submission.title,
                'selftext': submission.selftext,
                'score': submission.score,
                'url': submission.url,
                'comments': top_comments
            }
        except Exception as e:
            print(f"Error getting submission {submission_id}: {e}")
            return None
    
    def extract_locations_from_text(self, text: str) -> List[str]:
        """Extract potential location mentions from text"""
        # Nature-specific location patterns
        location_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+ (?:Park|Beach|Trail|Lake|Bridge|Mountain|Hill|Ridge|Canyon|Creek|Valley|Point|Head|Reserve|Preserve)\b',
            r'\b(?:Mount|Mt\.?|Lake|Point|Big|Little|Upper|Lower|North|South|East|West) [A-Z][a-z]+\b',
            r'\b[A-Z][a-z]+ (?:State Park|National Park|Regional Park|County Park|Open Space|Wilderness|Forest|Reserve)\b',
            r'\b[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+\b(?= (?:Park|Trail|Beach|Mountain|Lake|Canyon|Valley|Creek|Ridge|Point|Head|Reserve|Preserve))',
            r'\b[A-Z][a-z]+ (?:Park|Beach|Trail|Lake|Bridge|Mountain|Hill|Ridge|Canyon|Creek|Valley|Point|Head|Reserve|Preserve|Vista|Overlook|Viewpoint)\b',
            r'\b(?:Golden Gate|Muir Woods|Yosemite|Big Sur|Point Reyes|Marin Headlands|Angel Island|Alcatraz|Lands End|Ocean Beach|Baker Beach|Crissy Field|Presidio|Twin Peaks|Mission Peak|Mount Diablo|Castle Rock|Henry Cowell|Wilder Ranch|Santa Cruz Mountains|Los Gatos Creek|Almaden Quicksilver|Communications Hill|Sierra Vista|Ed Levin|Joseph Grant|Uvas Canyon|Mount Hamilton|Lick Observatory)\b',
        ]
        
        # Filter out common false positives
        false_positives = {
            'Street Parking', 'Road Bike', 'State Road', 'County Road', 'Open Space', 'State Park', 'County Park', 
            'National Park', 'Regional Park', 'City Hall', 'Fire Road', 'Parking Lot', 'Rest Area', 'Visitor Center',
            'Trail Head', 'Park Entrance', 'Day Use', 'Picnic Area', 'Restroom Area', 'Information Center'
        }
        
        locations = []
        for pattern in location_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if match not in false_positives and len(match) > 3:
                    locations.append(match)
        
        return list(set(locations))  # Remove duplicates
    
    def get_top_locations_by_score(self, results: List[Dict], top_n: int = 10) -> List[Dict]:
        """Extract top locations weighted by comment scores and frequency"""
        location_scores = {}
        
        for result in results:
            # Weight locations from highly upvoted posts
            post_weight = max(1, result['score'] / 10)  # Normalize post score
            
            # Add locations from post title/text with post weight
            for location in result['locations']:
                if location not in location_scores:
                    location_scores[location] = {'score': 0, 'mentions': 0, 'sources': []}
                
                location_scores[location]['score'] += post_weight
                location_scores[location]['mentions'] += 1
                location_scores[location]['sources'].append(f"Post: {result['title'][:50]}...")
            
            # Add locations from comments with comment score weight
            for comment in result['top_comments']:
                comment_locations = self.extract_locations_from_text(comment['body'])
                comment_weight = max(1, comment['score'] / 5)  # Normalize comment score
                
                for location in comment_locations:
                    if location not in location_scores:
                        location_scores[location] = {'score': 0, 'mentions': 0, 'sources': []}
                    
                    location_scores[location]['score'] += comment_weight * 1.5  # Comments weighted higher
                    location_scores[location]['mentions'] += 1
                    location_scores[location]['sources'].append(f"Comment (+{comment['score']}): {comment['body'][:50]}...")
        
        # Sort by score and return top N
        sorted_locations = sorted(
            location_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        return [
            {
                'name': location,
                'score': round(data['score'], 1),
                'mentions': data['mentions'],
                'sources': data['sources'][:3]  # Top 3 sources
            }
            for location, data in sorted_locations[:top_n]
        ]
    
    def scrape_for_locations(self, user_query: str, max_results: int = 5) -> List[Dict]:
        """Main method to scrape Reddit for locations based on user query"""
        print(f"Searching for: {user_query}")
        
        # Step 1: Search Reddit posts via Google
        reddit_urls = self.search_reddit_via_google(user_query, max_results)
        print(f"Found {len(reddit_urls)} Reddit URLs")
        
        results = []
        
        for url in reddit_urls:
            submission_id = self.extract_submission_id(url)
            if not submission_id:
                continue
            
            # Step 2: Get submission and comments
            submission_data = self.get_submission_with_comments(submission_id)
            if not submission_data:
                continue
            
            # Step 3: Extract locations from title, text, and comments
            all_text = f"{submission_data['title']} {submission_data['selftext']}"
            for comment in submission_data['comments']:
                all_text += f" {comment['body']}"
            
            locations = self.extract_locations_from_text(all_text)
            
            if locations:
                results.append({
                    'reddit_url': url,
                    'title': submission_data['title'],
                    'score': submission_data['score'],
                    'locations': locations,
                    'top_comments': submission_data['comments'][:3]  # Top 3 comments
                })
        
        return results

# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Reddit for nature locations')
    parser.add_argument('query', help='Search query (e.g., "hiking trails near golden gate")')
    parser.add_argument('--max-results', type=int, default=5, help='Maximum number of Reddit posts to process')
    parser.add_argument('--test-connection', action='store_true', help='Test Reddit connection first')
    
    args = parser.parse_args()
    
    scraper = RedditScraper()
    
    # Test Reddit connection if requested
    if args.test_connection:
        try:
            print("Testing Reddit connection...")
            subreddit = scraper.reddit.subreddit("hiking")
            print(f"Successfully connected to r/{subreddit.display_name}")
            
            # Test getting a post
            for submission in subreddit.hot(limit=1):
                print(f"Test post: {submission.title}")
                break
                
        except Exception as e:
            print(f"Reddit connection failed: {e}")
            exit(1)
    
    # Scrape for locations
    print(f"Searching for: '{args.query}'")
    results = scraper.scrape_for_locations(args.query, max_results=args.max_results)
    
    print(f"\n🎯 Found {len(results)} Reddit posts with locations")
    print("=" * 50)
    
    for i, result in enumerate(results, 1):
        print(f"\n📍 Result {i}:")
        print(f"Title: {result['title']}")
        print(f"Score: {result['score']} upvotes")
        print(f"Locations: {', '.join(result['locations'][:8])}")
        if len(result['locations']) > 8:
            print(f"... and {len(result['locations']) - 8} more")
        print(f"URL: {result['reddit_url']}")
        
        # Show top comment if available
        if result['top_comments']:
            top_comment = result['top_comments'][0]['body'][:150]
            print(f"💬 Top comment: {top_comment}...")
        print("-" * 40)
    
    # Get top locations by score
    top_locations = scraper.get_top_locations_by_score(results, top_n=10)
    
    if top_locations:
        print(f"\n🏆 TOP 10 LOCATIONS (by community score)")
        print("=" * 50)
        
        for i, location in enumerate(top_locations, 1):
            print(f"{i:2d}. {location['name']} (Score: {location['score']}, Mentions: {location['mentions']})")
            if location['sources']:
                print(f"    └─ {location['sources'][0]}")
        print("=" * 50)