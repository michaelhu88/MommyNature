import openai
import os
import json
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from google_places import GooglePlacesService

load_dotenv()

class GPTLocationExtractor:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("Warning: OPENAI_API_KEY not found in .env file")
            self.client = None
        else:
            self.client = openai.OpenAI(api_key=self.api_key)
        
        # Initialize Google Places service for verification
        self.places_service = GooglePlacesService()
    
    def extract_city_from_url(self, reddit_url: str) -> Optional[str]:
        """Extract city name from Reddit URL (e.g., r/SanJose -> San Jose)"""
        try:
            # Match pattern like /r/CityName/ or /r/BayArea/
            match = re.search(r'/r/([^/]+)/', reddit_url)
            if match:
                subreddit = match.group(1)
                
                # Handle common subreddit patterns
                city_mapping = {
                    'SanJose': 'San Jose',
                    'BayArea': 'Bay Area',
                    'SF': 'San Francisco',
                    'Oakland': 'Oakland',
                    'LosAngeles': 'Los Angeles',
                    'SanDiego': 'San Diego',
                    'Sacramento': 'Sacramento'
                }
                
                return city_mapping.get(subreddit, subreddit.replace('_', ' ').title())
            
            return None
        except:
            return None
    
    def extract_locations(self, transcript: Dict, city: str, category: str) -> Dict:
        """
        Extract and verify location names from Reddit transcript using GPT-4o-mini
        
        Args:
            transcript: Dict containing post and comments data
            city: City context for location extraction (required)
            category: Category of locations to extract (viewpoints, dog_parks, hiking_spots)
            
        Returns:
            Dict with raw_locations, deduplicated, and verified_locations
        """
        if not self.client:
            print("OpenAI client not available - skipping extraction")
            return {
                "raw_locations": [],
                "deduplicated": [],
                "verified_locations": [],
                "city_context": city,
                "category": category
            }
        
        try:
            print(f"🏙️ Using city: {city}")
            print(f"📂 Category: {category}")
            
            # Step 1: Build enhanced prompt with city and category context
            prompt = self._build_enhanced_prompt(transcript, city, category)
            
            # Step 2: Call GPT-4o-mini with enhanced prompt
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a location extraction expert. Extract only specific named places (parks, trails, mountains, viewpoints, beaches, etc.) from text. Return ONLY a JSON array of location names, nothing else."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=600,
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            # Step 3: Parse raw response
            gpt_response = response.choices[0].message.content.strip()
            raw_locations = self._parse_gpt_response(gpt_response)
            print(f"🤖 GPT extracted {len(raw_locations)} raw locations")
            
            # Step 4: Deduplicate locations
            deduplicated = self._deduplicate_locations(raw_locations)
            print(f"🔄 After deduplication: {len(deduplicated)} unique locations")
            
            # Step 5: Verify with Google Places API
            verified_locations = self._verify_with_google_places(deduplicated, city)
            print(f"✅ Verified {len(verified_locations)} locations with Google Places")
            
            return {
                "raw_locations": raw_locations,
                "deduplicated": deduplicated,
                "verified_locations": verified_locations,
                "city_context": city,
                "category": category
            }
            
        except Exception as e:
            print(f"❌ Error during GPT extraction: {e}")
            return {
                "raw_locations": [],
                "deduplicated": [],
                "verified_locations": [],
                "city_context": city,
                "category": category,
                "error": str(e)
            }
    
    def _build_enhanced_prompt(self, transcript: Dict, city: str, category: str) -> str:
        """Build enhanced extraction prompt with city and category context"""
        
        # Combine all text from post and comments
        all_text_parts = []
        
        # Add post content
        post = transcript.get('post', {})
        if post.get('title'):
            all_text_parts.append(f"Post Title: {post['title']}")
        if post.get('selftext'):
            all_text_parts.append(f"Post Text: {post['selftext']}")
        
        # Add comment content (limit to reasonable size)
        comments = transcript.get('comments', [])
        for i, comment in enumerate(comments[:20]):  # Limit to first 20 comments
            comment_text = comment.get('text', '').strip()
            if comment_text and len(comment_text) > 10:  # Skip very short comments
                all_text_parts.append(f"Comment {i+1}: {comment_text}")
        
        combined_text = "\n\n".join(all_text_parts)
        
        # Build enhanced prompt with city and category context
        category_instructions = {
            "viewpoints": "scenic overlooks, observation points, vista points, lookouts, scenic drives, mountain tops with views, bridges with views, and other places specifically known for their scenic views or panoramas",
            "dog_parks": "off-leash dog areas, dog parks, fenced dog runs, dog beaches, dog-friendly parks, canine areas, and other locations specifically designed for or welcoming to dogs",
            "hiking_spots": "hiking trails, trailheads, nature trails, walking paths, hiking destinations, mountain trails, forest paths, and other locations specifically for hiking or walking in nature"
        }
        
        category_focus = category_instructions.get(category, "outdoor locations")
        
        context_instruction = f"""
IMPORTANT: This discussion is about {category.replace('_', ' ')} in/around {city}.
- Do NOT include "{city}" itself in your results
- Focus ONLY on {category_focus}
- Exclude general city names, neighborhoods, or districts
- Extract specific named locations that match the category: {category.replace('_', ' ')}
- For {city}, prioritize well-known {category.replace('_', ' ')} mentioned in the discussion
"""
        
        prompt = f"""Extract specific location names for {category.replace('_', ' ')} mentioned in this Reddit discussion.
{context_instruction}
Return ONLY a JSON array of location names, nothing else. Example format:
["Mission Peak", "Castle Rock State Park", "Almaden Quicksilver"]

Reddit Discussion:
{combined_text}"""
        
        return prompt
    
    def _parse_gpt_response(self, response: str) -> List[str]:
        """Parse GPT response and extract location list"""
        try:
            # Try to parse as JSON directly
            locations = json.loads(response)
            
            # Validate it's a list
            if isinstance(locations, list):
                # Filter out empty strings and ensure all are strings
                filtered_locations = [
                    str(loc).strip() 
                    for loc in locations 
                    if loc and str(loc).strip()
                ]
                return filtered_locations
            else:
                print(f"❌ GPT response is not a list: {type(locations)}")
                return []
                
        except json.JSONDecodeError:
            print(f"❌ Could not parse GPT response as JSON: {response[:100]}...")
            
            # Fallback: try to extract array-like content
            try:
                # Look for content between brackets
                import re
                match = re.search(r'\[(.*?)\]', response, re.DOTALL)
                if match:
                    array_content = match.group(1)
                    # Simple parsing of quoted strings
                    locations = re.findall(r'"([^"]+)"', array_content)
                    return [loc.strip() for loc in locations if loc.strip()]
            except:
                pass
            
            return []
    
    def _deduplicate_locations(self, locations: List[str]) -> List[str]:
        """Remove duplicate locations with normalization"""
        seen = set()
        deduplicated = []
        
        for location in locations:
            if not location or not location.strip():
                continue
                
            # Normalize for comparison
            normalized = self._normalize_location_name(location.strip())
            
            if normalized.lower() not in seen:
                seen.add(normalized.lower())
                deduplicated.append(location.strip())
        
        return deduplicated
    
    def _normalize_location_name(self, location: str) -> str:
        """Normalize location name for deduplication"""
        # Convert to lowercase for comparison
        normalized = location.lower().strip()
        
        # Handle common variations
        normalized = normalized.replace('mt.', 'mount')
        normalized = normalized.replace('mt ', 'mount ')
        normalized = re.sub(r'\s+', ' ', normalized)  # Multiple spaces to single
        
        return normalized
    
    def _verify_with_google_places(self, locations: List[str], city: Optional[str] = None) -> List[Dict]:
        """Verify locations using Google Places API"""
        verified_locations = []
        
        if not self.places_service.api_key:
            print("⚠️ Google Places API key not available - skipping verification")
            # Return unverified locations in expected format
            return [{"name": loc, "verified": False, "google_data": None} for loc in locations]
        
        for location in locations:
            print(f"🔍 Verifying: {location}")
            
            try:
                # Build search query with city context
                search_query = location
                if city:
                    search_query = f"{location} {city}"
                
                # Search Google Places
                google_data = self.places_service.search_place(search_query)
                
                if google_data:
                    # Convert photo_names to photo_urls
                    photo_names = google_data.get('photo_names', [])
                    photo_urls = self.places_service.get_photo_urls(photo_names) if photo_names else []
                    
                    verified_locations.append({
                        "name": location,
                        "verified": True,
                        "google_data": {
                            "canonical_name": google_data.get('name', location),
                            "rating": google_data.get('rating'),
                            "review_count": google_data.get('review_count', 0),
                            "address": google_data.get('address', ''),
                            "place_id": google_data.get('place_id', ''),
                            "types": google_data.get('types', []),
                            "photo_urls": photo_urls
                        }
                    })
                    print(f"  ✅ Verified: {google_data.get('name', location)}")
                else:
                    print(f"  ❌ Not found in Google Places")
                    # Optionally include unverified locations
                    # verified_locations.append({
                    #     "name": location,
                    #     "verified": False,
                    #     "google_data": None
                    # })
                
            except Exception as e:
                print(f"  ⚠️ Error verifying {location}: {e}")
        
        return verified_locations

# Example usage and testing
if __name__ == "__main__":
    extractor = GPTLocationExtractor()
    
    # Test with sample transcript
    test_transcript = {
        "post": {
            "title": "Best hiking spots in Bay Area?",
            "selftext": "Looking for some good trails around San Jose. Heard Mission Peak is nice."
        },
        "comments": [
            {
                "text": "Mission Peak is great for sunrise! Also try Mount Hamilton and Castle Rock.",
                "score": 5
            },
            {
                "text": "Don't forget about Almaden Quicksilver Park - beautiful trails there.",
                "score": 3
            }
        ]
    }
    
    print("Testing GPT Location Extraction...")
    print("=" * 50)
    
    if extractor.client:
        result = extractor.extract_locations(test_transcript, city="San Jose", category="hiking_spots")
        print(f"Raw locations: {result['raw_locations']}")
        print(f"Deduplicated: {result['deduplicated']}")
        print(f"Verified locations: {len(result['verified_locations'])}")
        print(f"City: {result['city_context']}")
        print(f"Category: {result['category']}")
        for loc in result['verified_locations']:
            print(f"  - {loc['name']} (verified: {loc['verified']})")
    else:
        print("OpenAI API key not available - skipping test")