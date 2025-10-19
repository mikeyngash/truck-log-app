import requests
import polyline
import time
from django.core.cache import cache

class OSRMRouter:
    def __init__(self):
        self.base_url = "https://router.project-osrm.org/route/v1/driving"
        
    def get_route(self, origin, destination):
        """
        Get a route between two points using OSRM.
        
        Args:
            origin: Tuple of (lat, lon)
            destination: Tuple of (lat, lon)
            
        Returns:
            Dictionary with route details including distance, duration, and geometry
        """
        # Check cache first
        cache_key = f"route_{origin[0]}_{origin[1]}_{destination[0]}_{destination[1]}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Format coordinates for OSRM (lon,lat format)
        origin_str = f"{origin[1]},{origin[0]}"
        dest_str = f"{destination[1]},{destination[0]}"
        
        url = f"{self.base_url}/{origin_str};{dest_str}"
        params = {
            "overview": "full",
            "geometries": "polyline",
            "steps": "false"
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] != "Ok" or not data["routes"]:
                return None
                
            route = data["routes"][0]
            
            # Convert distance to miles (OSRM returns meters)
            distance_miles = route["distance"] / 1609.34
            
            # Convert duration to hours (OSRM returns seconds)
            duration_hours = route["duration"] / 3600
            
            # Decode the polyline to get coordinates
            geometry = polyline.decode(route["geometry"])
            
            # OSRM returns coordinates as [lat, lon]
            route_coords = geometry
            
            result = {
                "distance": distance_miles,
                "duration": duration_hours,
                "coordinates": route_coords
            }
            
            # Cache for 24 hours
            cache.set(cache_key, result, 60*60*24)
            
            return result
        except Exception as e:
            print(f"Routing error: {e}")
            return None
    
    def get_multi_point_route(self, points):
        """
        Get a route through multiple points.
        
        Args:
            points: List of (lat, lon) tuples
            
        Returns:
            Dictionary with route details
        """
        if len(points) < 2:
            return None
            
        # For multi-point routes, we'll calculate each segment and combine
        segments = []
        total_distance = 0
        total_duration = 0
        all_coordinates = []
        
        for i in range(len(points) - 1):
            route = self.get_route(points[i], points[i+1])
            if not route:
                return None
                
            segments.append(route)
            total_distance += route["distance"]
            total_duration += route["duration"]
            
            # Add coordinates (avoid duplicates at connection points)
            if i == 0:
                all_coordinates.extend(route["coordinates"])
            else:
                all_coordinates.extend(route["coordinates"][1:])
        
        return {
            "distance": total_distance,
            "duration": total_duration,
            "coordinates": all_coordinates,
            "segments": segments
        }

# Create a singleton instance
router = OSRMRouter()
