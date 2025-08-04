import praw
import re
import os
import time
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv
from google_places import GooglePlacesService
from gpt_summary import GPTSummaryService

load_dotenv()

class RedditScraper:
    # Known viewpoints and landmarks that should always be kept
    KNOWN_VIEWPOINTS = {
        'communications hill', 'mission peak', 'mount hamilton', 'mount umunhum',
        'twin peaks', 'coit tower', 'telegraph hill', 'russian hill', 
        'bernal heights', 'tank hill', 'corona heights', 'mount diablo',
        'mount tamalpais', 'lick observatory', 'sierra vista', 'grandview',
        'castle rock', 'monument peak', 'rose peak', 'flag hill'
    }
    
    def __init__(self, debug_mode=False):
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT'),
            check_for_async=False
        )
        self.places_service = GooglePlacesService()
        self.summary_service = GPTSummaryService()
        self.debug_mode = debug_mode
        self.cache_dir = os.path.join(os.path.dirname(__file__), "reddit_cache")
        self.locations_db_file = os.path.join(self.cache_dir, "locations_database.json")
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    
    def _load_locations_database(self) -> Dict:
        """Load the locations database from JSON file"""
        try:
            if os.path.exists(self.locations_db_file):
                with open(self.locations_db_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading locations database: {e}")
            return {}
    
    def _save_locations_database(self, database: Dict) -> None:
        """Save the locations database to JSON file"""
        try:
            with open(self.locations_db_file, 'w') as f:
                json.dump(database, f, indent=2)
            print(f"💾 Saved locations database")
        except Exception as e:
            print(f"Error saving locations database: {e}")
    
    def save_locations_for_city_category(self, city: str, category: str, locations: List[Dict]) -> None:
        """Save locations for a specific city and category"""
        database = self._load_locations_database()
        
        # Initialize city if it doesn't exist
        if city not in database:
            database[city] = {}
        
        # Save locations for this category
        database[city][category] = {
            'locations': locations,
            'updated_at': time.time(),
            'count': len(locations)
        }
        
        self._save_locations_database(database)
        print(f"💾 Saved {len(locations)} locations for {city} → {category}")
    
    def get_locations_for_city_category(self, city: str, category: str) -> List[Dict]:
        """Retrieve saved locations for a specific city and category"""
        database = self._load_locations_database()
        
        if city in database and category in database[city]:
            return database[city][category]['locations']
        return []
    
    def get_all_locations_for_city(self, city: str) -> Dict:
        """Retrieve all categories and locations for a specific city"""
        database = self._load_locations_database()
        return database.get(city, {})
    
    def extract_submission_id(self, reddit_url: str) -> Optional[str]:
        """Extract submission ID from Reddit URL"""
        match = re.search(r'/comments/([a-zA-Z0-9]+)', reddit_url)
        return match.group(1) if match else None
    
    def get_submission_with_comments(self, submission_id: str) -> Optional[Dict]:
        """Get Reddit submission with top comments"""
        try:
            submission = self.reddit.submission(id=submission_id)
            
            # Get top comments (fewer in debug mode)
            comment_limit = 2 if self.debug_mode else 10
            submission.comments.replace_more(limit=0)
            top_comments = []
            
            for comment in submission.comments[:comment_limit]:
                if hasattr(comment, 'body') and len(comment.body) > 20:
                    top_comments.append({
                        'body': comment.body,
                        'score': comment.score,
                        'author': str(comment.author) if comment.author else '[deleted]'
                    })
            
            data = {
                'title': submission.title,
                'selftext': submission.selftext,
                'score': submission.score,
                'url': submission.url,
                'comments': top_comments
            }
            
            # Add delay after processing to avoid rate limiting
            time.sleep(0.5 if self.debug_mode else 1)
            
            return data
        except Exception as e:
            print(f"Error getting submission {submission_id}: {e}")
            return None
    
    def extract_locations_from_text(self, text: str) -> List[Dict]:
        """Extract locations with context awareness using multi-pass approach"""
        all_locations = []
        
        # Pass 1: Recommendation context patterns
        recommendation_locations = self._extract_recommended_locations(text)
        all_locations.extend(recommendation_locations)
        
        # Pass 2: Descriptive context patterns  
        descriptive_locations = self._extract_described_locations(text)
        all_locations.extend(descriptive_locations)
        
        # Pass 3: Business and club locations
        business_locations = self._extract_business_locations(text)
        all_locations.extend(business_locations)
        
        # Pass 4: Quoted/emphasized locations
        quoted_locations = self._extract_quoted_locations(text)
        all_locations.extend(quoted_locations)
        
        # Pass 5: Traditional nature locations (extended)
        nature_locations = self._extract_nature_locations(text)
        all_locations.extend(nature_locations)
        
        # Pass 6: List context locations
        list_locations = self._extract_list_locations(text)
        all_locations.extend(list_locations)
        
        # Remove duplicates and combine scores
        return self._deduplicate_and_score_locations(all_locations)
    
    def _extract_recommended_locations(self, text: str) -> List[Dict]:
        """Extract locations with recommendation context"""
        patterns = [
            r'(?:go to (?:the )?|visit (?:the )?|check out (?:the )?|try (?:the )?|head to (?:the )?|stop by (?:the )?|been to (?:the )?)([A-Z][a-zA-Z\s]{5,40})(?=\s+(?:is|was|has|for|and|but|\.|,|!|\n|$))',
            r'(?:recommend (?:the )?|suggest (?:the )?|love (?:the )?)([A-Z][a-zA-Z\s]{5,40})(?=\s+(?:is|was|has|for|and|but|\.|,|!|\n|$))',
            r'(?:definitely (?:visit|check out|go to) (?:the )?)([A-Z][a-zA-Z\s]{5,40})(?=\s+(?:is|was|has|for|and|but|\.|,|!|\n|$))'
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = self._clean_location_name(match)
                if self._is_valid_location_name(cleaned):
                    locations.append({
                        'name': cleaned,
                        'context': 'recommendation',
                        'confidence': 0.9
                    })
        
        return locations
    
    def _extract_described_locations(self, text: str) -> List[Dict]:
        """Extract locations with descriptive context"""
        patterns = [
            r'([A-Z][a-zA-Z\s]{5,40})\s+(?:is (?:great|amazing|awesome|beautiful|perfect|nice|good|worth|recommended|incredible|fantastic|wonderful|excellent))',
            r'([A-Z][a-zA-Z\s]{5,40})\s+(?:has (?:great|amazing|beautiful|nice|good|incredible|fantastic|wonderful|excellent|stunning))',
            r'([A-Z][a-zA-Z\s]{5,40})\s+(?:offers (?:great|amazing|beautiful|nice|good|incredible|fantastic|wonderful|excellent|stunning))'
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                cleaned = self._clean_location_name(match)
                if self._is_valid_location_name(cleaned):
                    locations.append({
                        'name': cleaned,
                        'context': 'descriptive',
                        'confidence': 0.8
                    })
        
        return locations
    
    def _extract_business_locations(self, text: str) -> List[Dict]:
        """Extract business and club locations"""
        patterns = [
            # 4+ word clubs/businesses
            r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+(?:Club|Center|Resort|Lodge|Restaurant|Cafe|Bar|Grill|Course|Clubhouse))\b',
            r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+(?:Capital|Golf|Country|Sports|Recreation|Tennis|Athletic)\s+Club)\b',
            # 3+ word businesses
            r'\b([A-Z][a-z]{2,}\s+(?:Golf|Country|Sports|Athletic|Tennis|Recreation)\s+Club)\b',
            r'\b([A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}\s+(?:Restaurant|Cafe|Bar|Grill|Course|Resort|Lodge|Center))\b'
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if self._is_valid_location_name(match):
                    locations.append({
                        'name': match,
                        'context': 'business',
                        'confidence': 0.85
                    })
        
        return locations
    
    def _extract_quoted_locations(self, text: str) -> List[Dict]:
        """Extract quoted or emphasized locations"""
        patterns = [
            r'"([A-Z][^"]{5,40})"',  # Double quotes
            r"'([A-Z][^']{5,40})'",  # Single quotes
            r'\*([A-Z][^*]{5,40})\*',  # Asterisk emphasis
            r'`([A-Z][^`]{5,40})`'   # Backtick code formatting
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                cleaned = self._clean_location_name(match)
                if self._is_valid_location_name(cleaned):
                    locations.append({
                        'name': cleaned,
                        'context': 'quoted',
                        'confidence': 0.75
                    })
        
        return locations
    
    def _extract_nature_locations(self, text: str) -> List[Dict]:
        """Extract traditional nature locations with extended word limits"""
        patterns = [
            # Known Bay Area locations
            r'\b(?:Mission Peak|Mount Diablo|Mount Hamilton|Mount Tamalpais|Twin Peaks|Communications Hill|Sierra Vista|Lick Observatory|Golden Gate Bridge|Golden Gate|Muir Woods|Point Reyes|Big Sur|Yosemite|Castle Rock|Henry Cowell|Almaden Quicksilver|Los Gatos Creek|Coyote Hills|Ed Levin|Joseph Grant|Uvas Canyon|Fremont Peak|Pinnacles|Santa Teresa|Rancho San Antonio|Stevens Creek|Skyline Ridge|Russian Ridge|Windy Hill|Coal Creek|Purisima Creek|Huddart Park|Wunderlich Park|Woodside Store|Foothills Park|Arastradero Preserve|Pearson-Arastradero|Palo Alto Baylands|Shoreline Amphitheatre|Baylands Park|Don Edwards|Coyote Creek|Alviso Marina|Sunol Wilderness|Ohlone Wilderness|Rose Peak|Monument Peak|Flag Hill|Brushy Peak|Mt Umunhum|Belgatos Park|Santa Teresa County Park|Joseph D Grant Park|Fremont Older|Dutch Flat Trail|Grandview)\b',
            
            # Mount/Mt prefix - extended
            r'\b(?:Mount|Mt\.?)\s+([A-Z][a-z]{3,}(?:\s+[A-Z][a-z]{3,})*)\b',
            
            # Extended nature locations - up to 4 words
            r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,4})\s+(?:Park|Trail|Hill|Peak|Observatory|Reserve|Preserve|Wilderness|Mountain|Ridge|Point|Lake|Creek|Valley|Beach)\b',
            
            # Two+ proper nouns + nature suffix
            r'\b([A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,}){1,3})\s+(?:County|State|Regional|Open Space)\s+(?:Park|Preserve|Wilderness)\b'
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Handle both full matches and captured groups
                location_name = match if isinstance(match, str) else match[0] if match else ""
                if location_name and self._is_valid_location_name(location_name):
                    locations.append({
                        'name': location_name,
                        'context': 'nature',
                        'confidence': 0.7
                    })
        
        return locations
    
    def _extract_list_locations(self, text: str) -> List[Dict]:
        """Extract locations from bulleted or numbered lists"""
        patterns = [
            r'(?:^\s*[-•*]\s*|^\s*\d+\.\s*)([A-Z][a-zA-Z\s]{5,40})(?:\s*[-:]|\n|$)',  # List items
            r'\n\s*([A-Z][a-zA-Z\s]{5,40})\s*[-:]\s*'  # Lines with colons/dashes
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                cleaned = self._clean_location_name(match)
                if self._is_valid_location_name(cleaned):
                    locations.append({
                        'name': cleaned,
                        'context': 'list',
                        'confidence': 0.6
                    })
        
        return locations
    
    def _clean_location_name(self, name: str) -> str:
        """Clean and normalize location names"""
        # Remove leading/trailing whitespace
        cleaned = name.strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['the ', 'maybe ', 'perhaps ', 'possibly ', 'probably ', 'about ', 'called ', 'near ']
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):]
        
        # Remove trailing punctuation and connectors
        cleaned = re.sub(r'[,.\-!?;]+$', '', cleaned)
        cleaned = re.sub(r'\s+(and|or|but|with|for|in|at|on|to|from)$', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def _is_valid_location_name(self, name: str) -> bool:
        """Enhanced validation for location names"""
        if not name or len(name) < 4:
            return False
        
        name_lower = name.lower().strip()
        
        # Must contain at least one capital letter
        if not any(c.isupper() for c in name):
            return False
        
        # Reject if starts with common non-location words
        bad_prefixes = ['know ', 'the ', 'a ', 'an ', 'you ', 'i ', 'we ', 'they ', 'it ',
                       'can ', 'could ', 'might ', 'should ', 'will ', 'would ',
                       'and ', 'or ', 'but ', 'so ', 'if ', 'when ', 'where ',
                       'maybe ', 'perhaps ', 'possibly ', 'probably ', 'definitely ',
                       'try ', 'check ', 'visit ', 'go ', 'see ', 'find ', 'about ']
        
        for prefix in bad_prefixes:
            if name_lower.startswith(prefix):
                return False
        
        # Reject parking-related terms
        parking_words = ['parking', 'park here', 'park there', 'can park', 'could park']
        for bad_word in parking_words:
            if bad_word in name_lower:
                return False
        
        return True
    
    def _deduplicate_and_score_locations(self, locations: List[Dict]) -> List[str]:
        """Remove duplicates and return location names"""
        unique_locations = {}
        
        for loc in locations:
            name = loc['name']
            normalized_name = self._normalize_location_name(name)
            
            if normalized_name not in unique_locations:
                unique_locations[normalized_name] = {
                    'name': name,
                    'contexts': [loc['context']],
                    'max_confidence': loc['confidence']
                }
            else:
                # Keep the name with highest confidence
                if loc['confidence'] > unique_locations[normalized_name]['max_confidence']:
                    unique_locations[normalized_name]['name'] = name
                    unique_locations[normalized_name]['max_confidence'] = loc['confidence']
                unique_locations[normalized_name]['contexts'].append(loc['context'])
        
        # Return list of unique location names, sorted by confidence
        sorted_locations = sorted(
            unique_locations.values(),
            key=lambda x: x['max_confidence'],
            reverse=True
        )
        
        return [loc['name'] for loc in sorted_locations]
    
    
    def _normalize_location_name(self, location: str) -> str:
        """Basic normalization - remove prefixes and handle common abbreviations"""
        # Clean and normalize - remove common prefixes first
        cleaned = location.strip()
        cleaned_lower = cleaned.lower()
        
        # Remove common prefixes that aren't part of location names
        prefixes_to_remove = ['the ', 'maybe ', 'perhaps ', 'possibly ', 'probably ', 'about ', 'called ', 'near ']
        for prefix in prefixes_to_remove:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                cleaned_lower = cleaned.lower()
                break
        
        # Handle common abbreviations - basic normalization only
        if cleaned_lower.startswith('mt ') or cleaned_lower.startswith('mount ') or cleaned_lower.startswith('mt. '):
            # Standardize Mt./Mount formatting
            parts = cleaned_lower.replace('mount ', 'mt ').replace('mt. ', 'mt ').split()
            if len(parts) >= 2:
                return f"Mt {parts[1].title()}"
        
        # Capitalize properly (Title Case)
        return cleaned.title()
    
    def get_top_locations_by_score(self, results: List[Dict], top_n: int = 10, category: str = "") -> List[Dict]:
        """Extract top locations weighted by comment scores and frequency"""
        location_scores = {}
        
        for result in results:
            # Weight locations from highly upvoted posts
            post_weight = max(1, result['score'] / 10)  # Normalize post score
            
            # Add locations from post title/text with post weight
            for location in result['locations']:
                normalized_name = self._normalize_location_name(location)
                
                if normalized_name not in location_scores:
                    location_scores[normalized_name] = {'score': 0, 'mentions': 0, 'sources': [], 'original_name': location}
                
                location_scores[normalized_name]['score'] += post_weight
                location_scores[normalized_name]['mentions'] += 1
                location_scores[normalized_name]['sources'].append(f"Post: {result['title'][:50]}...")
            
            # Add locations from comments with comment score weight
            for comment in result['top_comments']:
                comment_locations = self.extract_locations_from_text(comment['body'])
                comment_weight = max(1, comment['score'] / 5)  # Normalize comment score
                
                for location in comment_locations:
                    normalized_name = self._normalize_location_name(location)
                    
                    if normalized_name not in location_scores:
                        location_scores[normalized_name] = {'score': 0, 'mentions': 0, 'sources': [], 'original_name': location}
                    
                    location_scores[normalized_name]['score'] += comment_weight * 1.5  # Comments weighted higher
                    location_scores[normalized_name]['mentions'] += 1
                    location_scores[normalized_name]['sources'].append(f"Comment (+{comment['score']}): {comment['body'][:50]}...")
        
        # Sort by score and return top N
        sorted_locations = sorted(
            location_scores.items(), 
            key=lambda x: x[1]['score'], 
            reverse=True
        )
        
        reddit_locations = [
            {
                'name': data['original_name'],  # Use the original name for display
                'score': round(data['score'], 1),
                'mentions': data['mentions'],
                'sources': data['sources'][:3]  # Top 3 sources
            }
            for _, data in sorted_locations[:top_n]
        ]
        
        # Use Google Places to validate and enhance locations with city context
        print("🔍 Validating locations with Google Places API...")
        # Get city context from the original results since reddit_locations doesn't have it
        city_context = results[0].get('city_context', '') if results else ''
        print(f"Using city context: '{city_context}'")
        validated_locations = self._validate_locations_with_google_places(reddit_locations, city_context, category)
        
        return validated_locations
    
    def _validate_locations_with_google_places(self, locations: List[Dict], city_context: str = "", category: str = "") -> List[Dict]:
        """Validate and enhance locations using Google Places API with strict filtering"""
        validated_locations = []
        
        for location in locations:
            location_name = location['name']
            print(f"  Validating: {location_name}")
            
            # Use the provided city context directly
            search_query = f"{location_name} {city_context}".strip()
            print(f"    Searching: {search_query}")
            
            # Try to find the location in Google Places
            google_data = self.places_service.search_place(search_query)
            
            if google_data:
                canonical_name = google_data['name']
                review_count = google_data.get('review_count', 0)
                place_types = google_data.get('types', [])
                
                # Apply strict filtering criteria with category context
                if not self._is_valid_google_place(google_data, location_name, category):
                    print(f"    ❌ Filtered out: {canonical_name} (too general or insufficient reviews)")
                    continue
                
                # Location passed validation
                print(f"    ✅ Found: {canonical_name}")
                
                # Calculate enhanced combined score with context awareness
                google_score = self.places_service.calculate_google_score(
                    google_data.get('rating', 0),
                    review_count
                )
                
                reddit_score = location['score']
                
                # Context-aware scoring boost
                context_boost = self._get_context_boost(location.get('context', 'nature'))
                type_boost = self._get_type_boost(place_types)
                
                combined_score = (reddit_score * 0.4) + (google_score * 0.6)
                final_score = combined_score * context_boost * type_boost
                
                validated_location = {
                    'name': canonical_name,  # Use Google's canonical name
                    'score': round(final_score, 1),
                    'reddit_score': reddit_score,
                    'google_score': google_score,
                    'context_boost': context_boost,
                    'type_boost': type_boost,
                    'mentions': location['mentions'],
                    'sources': location['sources'],
                    'google_rating': google_data.get('rating'),
                    'google_reviews': review_count,
                    'google_types': place_types,
                    'address': google_data.get('address', ''),
                    'place_id': google_data.get('place_id', ''),
                    'validated': True
                }
                
                validated_locations.append(validated_location)
            else:
                # Location not found in Google Places - skip it
                print(f"    ❌ Not found in Google Places: {location_name}")
        
        # Sort by final score
        validated_locations.sort(key=lambda x: x['score'], reverse=True)
        
        print(f"✅ Validated {len(validated_locations)} out of {len(locations)} locations")
        return validated_locations
    
    def _is_valid_google_place(self, google_data: Dict, original_name: str, category: str = "") -> bool:
        """Apply category-aware filtering criteria to Google Places results"""
        review_count = google_data.get('review_count', 0)
        place_types = google_data.get('types', [])
        original_name_lower = original_name.lower().strip()
        
        # Check if it's a known landmark - always keep these
        if original_name_lower in self.KNOWN_VIEWPOINTS:
            print(f"    🏔️  Known landmark: {original_name}")
            return True
        
        # For viewpoint contexts, be more lenient with geographic features
        if category.lower() in ['viewpoints', 'viewpoint']:
            # Allow neighborhoods/political areas if they have elevation keywords
            if any(ptype in place_types for ptype in ['neighborhood', 'political', 'sublocality']):
                elevation_keywords = ['hill', 'peak', 'mount', 'mountain', 'heights', 'ridge', 'summit', 'overlook', 'vista']
                if any(keyword in original_name_lower for keyword in elevation_keywords):
                    print(f"    🏔️  Geographic viewpoint: {original_name}")
                    return True
        
        # For hiking contexts, allow trails and natural features
        if category.lower() in ['hiking', 'hiking_trails', 'trails']:
            trail_keywords = ['trail', 'path', 'creek', 'wilderness', 'preserve']
            if any(keyword in original_name_lower for keyword in trail_keywords):
                return True
        
        # Require minimum reviews for credibility (unless it's a well-known natural feature)
        if review_count < 3:
            # Allow natural features with 0 reviews if they have specific types
            natural_types = ['natural_feature', 'park', 'tourist_attraction']
            if not any(nat_type in place_types for nat_type in natural_types):
                return False
        
        # Block overly general geographic areas
        blocked_types = ['colloquial_area', 'country', 'administrative_area_level_1']
        if any(blocked_type in place_types for blocked_type in blocked_types):
            # Only allow if it has significant reviews (indicating it's a real destination)
            if review_count < 20:
                return False
        
        # Be more lenient with 'political' type for geographic features in viewpoint contexts
        if 'political' in place_types:
            if category.lower() in ['viewpoints', 'viewpoint'] and review_count >= 0:
                # Allow political areas that might be legitimate viewpoints
                return True
            elif review_count < 20:
                return False
        
        # Block general localities unless they have many reviews
        if 'locality' in place_types and review_count < 10:
            return False
        
        return True
    
    def _get_context_boost(self, context: str) -> float:
        """Get scoring boost based on extraction context"""
        context_boosts = {
            'recommendation': 1.5,  # "check out", "visit", "recommend"
            'descriptive': 1.3,     # "X is great", "X has amazing"
            'business': 1.2,        # Club, restaurant patterns
            'quoted': 1.1,          # Quoted or emphasized
            'nature': 1.0,          # Traditional nature patterns
            'list': 0.9             # List items
        }
        return context_boosts.get(context, 1.0)
    
    def _get_type_boost(self, place_types: List[str]) -> float:
        """Get scoring boost based on Google Place types"""
        # Prioritize specific venue types
        high_priority_types = ['point_of_interest', 'establishment', 'tourist_attraction', 
                              'natural_feature', 'amusement_park', 'park']
        
        if any(good_type in place_types for good_type in high_priority_types):
            return 1.2
        
        # Penalize overly general areas
        general_types = ['political', 'colloquial_area', 'locality']
        if any(general_type in place_types for general_type in general_types):
            return 0.7
        
        return 1.0
    
    def extract_top_locations_from_url(self, reddit_url: str, city: str, category: str, target_count: int = 10) -> List[Dict]:
        """
        Extract top locations from a single Reddit URL using universal logic
        
        Args:
            reddit_url: Reddit post URL to scrape
            city: City name for organizational purposes (e.g., "San Jose, CA")
            category: Category for organizational purposes (e.g., "viewpoints", "hiking_trails")
            target_count: Number of top locations to return (default: 10)
        
        Returns:
            List of top locations with scores and metadata
        """
        print(f"🔍 Extracting locations from Reddit URL for {city} → {category}")
        
        # Extract submission ID from URL
        submission_id = self.extract_submission_id(reddit_url)
        if not submission_id:
            print(f"❌ Could not extract submission ID from URL: {reddit_url}")
            return []
        
        # Get submission and comments using existing method
        submission_data = self.get_submission_with_comments(submission_id)
        if not submission_data:
            print(f"❌ Could not fetch submission data for ID: {submission_id}")
            return []
        
        # Extract locations from all text using existing logic
        all_text = f"{submission_data['title']} {submission_data['selftext']}"
        for comment in submission_data['comments']:
            all_text += f" {comment['body']}"
        
        locations = self.extract_locations_from_text(all_text)
        print(f"📍 Found {len(locations)} location mentions")
        
        # Create results structure compatible with existing scoring method
        results = [{
            'title': submission_data['title'],
            'score': submission_data['score'],
            'locations': locations,
            'top_comments': submission_data['comments'],
            'url': reddit_url
        }]
        
        # Use existing scoring logic to get top locations
        top_locations = self.get_top_locations_by_score(results, top_n=target_count, category=category)
        
        # Add metadata for storage
        for location in top_locations:
            location['city'] = city
            location['category'] = category
            location['source_url'] = reddit_url
        
        print(f"✅ Extracted {len(top_locations)} top locations for {city} → {category}")
        
        # Automatically save to database
        self.save_locations_for_city_category(city, category, top_locations)
        
        return top_locations
    
# Example usage and testing
if __name__ == "__main__":
    # Use debug mode for faster testing
    scraper = RedditScraper(debug_mode=True)
    
    # Test with new URL-based approach
    print("🔍 Testing Reddit scraper with URL approach...")
    test_url = "https://reddit.com/r/bayarea/comments/example/best_viewpoints"
    
    try:
        locations = scraper.extract_top_locations_from_url(test_url, "San Jose, CA", "viewpoints")
        print(f"✅ Extracted {len(locations)} locations")
        for i, location in enumerate(locations[:5], 1):
            print(f"  {i}. {location['name']} (Score: {location['score']})")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("Note: Provide a real Reddit URL for testing")