import openai
import os
from typing import Dict, List, Optional
from dotenv import load_dotenv
import json

load_dotenv()

class GPTSummaryService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in .env file")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
    
    def generate_location_summary(self, location_data: Dict, reddit_comments: List[str] = None) -> Optional[str]:
        """
        Generate a warm, mom-style summary for a nature location
        
        Args:
            location_data: Dict with name, rating, address, etc.
            reddit_comments: List of relevant Reddit comments about the location
        """
        if not self.client:
            return None
        
        # Prepare context from the location data
        location_name = location_data.get('name', 'Unknown location')
        rating = location_data.get('google_rating')
        review_count = location_data.get('google_reviews', 0)
        address = location_data.get('address', '')
        location_types = location_data.get('google_types', [])
        
        # Build context string
        context_parts = [f"Location: {location_name}"]
        
        if address:
            context_parts.append(f"Address: {address}")
        
        if rating and review_count:
            context_parts.append(f"Google Rating: {rating}/5 stars with {review_count} reviews")
        
        if location_types:
            context_parts.append(f"Type: {', '.join(location_types[:3])}")
        
        if reddit_comments:
            context_parts.append("Reddit community insights:")
            for i, comment in enumerate(reddit_comments[:3], 1):
                # Clean and truncate comments
                clean_comment = comment.strip()[:200]
                context_parts.append(f"{i}. {clean_comment}")
        
        context = "\n".join(context_parts)
        
        # Create the prompt for mom-style advice
        prompt = f"""You are a caring, experienced mom writing location recommendations for other parents and families who love nature. 

Write a warm, practical, and encouraging 2-3 sentence summary for this location. Your tone should be:
- Friendly and maternal 
- Practical with helpful tips
- Enthusiastic but honest
- Focus on what makes it special for families or nature lovers
- Include any practical considerations (parking, difficulty, best times to visit)

Location Information:
{context}

Write a summary that sounds like advice from a trusted friend who's been there with her family:"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful, caring mom who gives great outdoor recommendations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"Error generating summary for {location_name}: {e}")
            # Return fallback summary instead of None
            return self._create_fallback_summary(location_data)
    
    def enhance_locations_with_summaries(self, locations: List[Dict], reddit_posts: List[Dict] = None) -> List[Dict]:
        """Add GPT-generated summaries to location data"""
        enhanced_locations = []
        
        for location in locations:
            # Find relevant Reddit comments for this location
            relevant_comments = []
            if reddit_posts:
                location_name = location['name'].lower()
                for post in reddit_posts:
                    for comment in post.get('top_comments', []):
                        comment_text = comment.get('body', '').lower()
                        if location_name in comment_text:
                            relevant_comments.append(comment.get('body', ''))
            
            # Generate summary
            summary = self.generate_location_summary(location, relevant_comments[:3])
            
            # Add to location data
            enhanced_location = location.copy()
            enhanced_location['mom_summary'] = summary
            enhanced_locations.append(enhanced_location)
        
        return enhanced_locations
    
    def generate_batch_summaries(self, locations: List[Dict]) -> Dict[str, str]:
        """Generate summaries for multiple locations efficiently"""
        summaries = {}
        
        for location in locations:
            if self.client:
                summary = self.generate_location_summary(location)
                summaries[location['name']] = summary
            else:
                # Fallback summary when no API key
                summaries[location['name']] = self._create_fallback_summary(location)
        
        return summaries
    
    def _create_fallback_summary(self, location: Dict) -> str:
        """Create a basic summary when GPT is not available"""
        name = location.get('name', 'This location')
        rating = location.get('google_rating')
        review_count = location.get('google_reviews', 0)
        
        if rating and review_count:
            return f"{name} is a wonderful spot that visitors love, with {rating}/5 stars from {review_count} reviews. It's definitely worth checking out for your next outdoor adventure!"
        else:
            return f"{name} is a beautiful natural area that the Reddit community recommends. Perfect for those looking to explore something special!"

# Example usage and testing
if __name__ == "__main__":
    summary_service = GPTSummaryService()
    
    # Test location data
    test_location = {
        'name': 'Lick Observatory',
        'google_rating': 4.7,
        'google_reviews': 619,
        'address': '7281 Mt Hamilton Rd, Mt Hamilton, CA 95140, USA',
        'google_types': ['tourist_attraction', 'point_of_interest']
    }
    
    test_comments = [
        "Amazing views of the valley! Bring a jacket though, it gets cold up there.",
        "Perfect spot for stargazing. The drive up is winding but totally worth it.",
        "Great educational experience for kids. The telescopes are incredible!"
    ]
    
    print("Testing GPT Summary Service...")
    print("=" * 50)
    
    if summary_service.client:
        summary = summary_service.generate_location_summary(test_location, test_comments)
        print(f"Location: {test_location['name']}")
        print(f"Mom's Summary: {summary}")
    else:
        print("OpenAI API key not available - using fallback summaries")
        fallback = summary_service._create_fallback_summary(test_location)
        print(f"Location: {test_location['name']}")
        print(f"Fallback Summary: {fallback}")