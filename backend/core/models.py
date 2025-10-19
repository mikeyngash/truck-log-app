from django.db import models

class Trip(models.Model):
    current_location = models.CharField(max_length=255)
    current_location_coords = models.JSONField(null=True, blank=True)
    pickup_location = models.CharField(max_length=255)
    pickup_location_coords = models.JSONField(null=True, blank=True)
    dropoff_location = models.CharField(max_length=255)
    dropoff_location_coords = models.JSONField(null=True, blank=True)
    current_cycle_hours = models.FloatField(default=0)
    use_sleeper_berth = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class LogEntry(models.Model):
    class Status(models.TextChoices):
        OFF_DUTY = 'Off-Duty', 'Off-Duty'
        SLEEPER_BERTH = 'Sleeper Berth', 'Sleeper Berth'
        DRIVING = 'Driving', 'Driving'
        ON_DUTY = 'On-Duty', 'On-Duty'

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    remarks = models.TextField()
    grid_positions = models.JSONField(null=True, blank=True)  # For grid drawing
