import requests
import time
from django.core.cache import cache

class NominatimGeocoder:
    def __init__(self, user_agent="truck-log-app"):
        self.user_agent = user_agent
        self.base_url = "https://nominatim.openstreetmap.org/search"
        
    def geocode(self, location_name):
        """Get coordinates for a location name with caching."""
        # Check cache first
        cache_key = f"geocode_{location_name}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Respect Nominatim usage policy (max 1 request per second)
        time.sleep(1)
        
        params = {
            "q": location_name,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": self.user_agent
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()
            
            if results:
                result = results[0]
                coordinates = (float(result["lat"]), float(result["lon"]))
                # Cache for 24 hours
                cache.set(cache_key, coordinates, 60*60*24)
                return coordinates
            return None
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
    
    def search(self, query, limit=5):
        """Search for locations matching a query."""
        # Respect Nominatim usage policy
        time.sleep(1)
        
        params = {
            "q": query,
            "format": "json",
            "limit": limit,
        }
        headers = {
            "User-Agent": self.user_agent
        }
        
        try:
            response = requests.get(self.base_url, params=params, headers=headers)
            response.raise_for_status()
            results = response.json()
            
            return [
                {
                    "name": result["display_name"],
                    "lat": float(result["lat"]),
                    "lon": float(result["lon"])
                }
                for result in results
            ]
        except Exception as e:
            print(f"Location search error: {e}")
            return []

# Create a singleton instance
geocoder = NominatimGeocoder()
