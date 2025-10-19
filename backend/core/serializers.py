from rest_framework import serializers
from .models import Trip, LogEntry
from .geocoding import geocoder

class TripSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = '__all__'
        read_only_fields = ['current_location_coords', 'pickup_location_coords', 'dropoff_location_coords']

    def validate(self, data):
        # Validate that locations are different
        if data.get('current_location') == data.get('pickup_location'):
            raise serializers.ValidationError("Current location and pickup location must be different.")
        if data.get('pickup_location') == data.get('dropoff_location'):
            raise serializers.ValidationError("Pickup location and dropoff location must be different.")
        if data.get('current_location') == data.get('dropoff_location'):
            raise serializers.ValidationError("Current location and dropoff location must be different.")

        # Validate current_cycle_hours is non-negative
        if data.get('current_cycle_hours', 0) < 0:
            raise serializers.ValidationError("Current cycle hours cannot be negative.")

        # Geocode locations
        for field in ['current_location', 'pickup_location', 'dropoff_location']:
            location = data.get(field)
            if location:
                coords = geocoder.geocode(location)
                if not coords:
                    raise serializers.ValidationError(f"Could not geocode {field.replace('_', ' ')}. Please enter a valid location.")
                data[f"{field}_coords"] = coords

        return data

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'
