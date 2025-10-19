import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from .models import Trip
from .serializers import TripSerializer
from .services import calculate_route_and_logs
from .geocoding import geocoder

logger = logging.getLogger(__name__)

class TripView(APIView):
    def post(self, request):
        logger.info(f"Received data: {request.data}")
        try:
            serializer = TripSerializer(data=request.data)
            if serializer.is_valid():
                trip = serializer.save()
                logger.info(f"Trip saved with ID: {trip.id}")
                result = calculate_route_and_logs(trip)
                logger.info("Route and logs calculated successfully")
                
                # Add location data to the response
                result['locations'] = [
                    {
                        'name': trip.current_location,
                        'lat': trip.current_location_coords[0],
                        'lon': trip.current_location_coords[1]
                    },
                    {
                        'name': trip.pickup_location,
                        'lat': trip.pickup_location_coords[0],
                        'lon': trip.pickup_location_coords[1]
                    },
                    {
                        'name': trip.dropoff_location,
                        'lat': trip.dropoff_location_coords[0],
                        'lon': trip.dropoff_location_coords[1]
                    }
                ]
                
                return Response(result)
            logger.error(f"Serializer validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.exception(f"Exception in trip creation: {e}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def location_search(request):
    query = request.query_params.get('q', '')
    if len(query) < 3:
        return Response({"error": "Query must be at least 3 characters"}, status=400)
    
    results = geocoder.search(query)
    return Response(results)
