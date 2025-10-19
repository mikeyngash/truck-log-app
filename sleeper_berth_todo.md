# Sleeper Berth Support Implementation TODO

- [x] Add `use_sleeper_berth` BooleanField to Trip model in models.py
- [x] Modify break insertion logic in services.py to split eligible breaks (>=9 hours) into 'Sleeper Berth' (7 hours) and 'Off-Duty' (remainder >=2 hours) if use_sleeper_berth is True
- [x] Run Django makemigrations and migrate
- [x] Restart Django server if necessary (server reloaded automatically)
- [x] Test the sleeper berth feature with a sample trip
