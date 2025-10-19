# Testing Guide for Enhanced Location Features

## Prerequisites

- Backend server running on http://127.0.0.1:8000
- Frontend server running on http://localhost:3000

## Test Cases

### 1. Location Autocomplete Testing

#### Test 1.1: Current Location Autocomplete

1. Open http://localhost:3000 in your browser
2. Click on the "Current Location" input field
3. Type "Chi" (3 characters minimum)
4. **Expected Result**: A dropdown should appear with suggestions like:
   - "Chicago, Cook County, Illinois, United States"
   - Other cities starting with "Chi"
5. Click on one of the suggestions
6. **Expected Result**: The input field should be filled with the selected location

#### Test 1.2: Pickup Location Autocomplete

1. Click on the "Pickup Location" input field
2. Type "New York"
3. **Expected Result**: Dropdown shows suggestions including:
   - "City of New York, New York, United States"
   - "New York, United States" (the state)
4. Select a suggestion
5. **Expected Result**: Input field updates with selection

#### Test 1.3: Dropoff Location Autocomplete

1. Click on the "Dropoff Location" input field
2. Type "Los Angeles"
3. **Expected Result**: Dropdown shows Los Angeles suggestions
4. Select one
5. **Expected Result**: Input field updates

#### Test 1.4: International Locations

1. Try typing "London" in any location field
2. **Expected Result**: Should show London, UK and other Londons worldwide
3. Try "Paris", "Tokyo", "Sydney"
4. **Expected Result**: All should work with international locations

### 2. Form Submission Testing

#### Test 2.1: Basic Trip Generation

1. Fill in all three location fields using autocomplete:
   - Current Location: "Chicago, IL"
   - Pickup Location: "Milwaukee, WI"
   - Dropoff Location: "Madison, WI"
2. Leave "Current Cycle Hours" at 0
3. Leave "Use Sleeper Berth" unchecked
4. Click "Generate Route & Logs"
5. **Expected Results**:
   - Loading indicator appears
   - After a few seconds, results panel shows:
     - Route: Chicago, IL → Milwaukee, WI → Madison, WI
     - Total Distance: ~167 miles
     - Total Duration: calculated hours
   - Log grid displays with entries
   - Map shows the route with multiple waypoints

#### Test 2.2: Long Distance Trip

1. Enter:
   - Current Location: "New York, NY"
   - Pickup Location: "Chicago, IL"
   - Dropoff Location: "Los Angeles, CA"
2. Set Current Cycle Hours: 5
3. Check "Use Sleeper Berth"
4. Submit
5. **Expected Results**:
   - Much longer distance (~2,800 miles)
   - Multiple rest breaks in the log
   - Sleeper berth entries visible
   - Route follows actual highways

#### Test 2.3: International Trip (if supported)

1. Try locations in different countries
2. **Expected Result**: Should geocode successfully but routing might fail (OSRM primarily covers roads with data)

### 3. API Endpoint Testing

#### Test 3.1: Location Search API

```bash
curl "http://127.0.0.1:8000/api/locations/search/?q=Boston"
```

**Expected Response**:

```json
[
  {
    "name": "Boston, Suffolk County, Massachusetts, United States",
    "lat": 42.3554334,
    "lon": -71.060511
  }
]
```

#### Test 3.2: Trip Creation API

```bash
python test_trip_api.py
```

**Expected Output**:

- Location search returns results
- Trip creation returns 200 status
- Response includes route, distance, duration, logs, and route_coordinates

### 4. Error Handling Testing

#### Test 4.1: Invalid Location

1. Type a nonsense location like "asdfghjkl"
2. Try to submit
3. **Expected Result**: Backend should return an error about geocoding failure

#### Test 4.2: Network Error

1. Stop the Django backend server
2. Try to use autocomplete
3. **Expected Result**: Console shows error, but app doesn't crash
4. Try to submit form
5. **Expected Result**: Error message displayed to user

#### Test 4.3: Minimum Character Requirement

1. Type only 1 or 2 characters in a location field
2. **Expected Result**: No suggestions appear (minimum 3 characters required)

### 5. UI/UX Testing

#### Test 5.1: Dropdown Behavior

1. Click in a location field and type
2. **Expected Result**: Dropdown appears
3. Click outside the dropdown
4. **Expected Result**: Dropdown disappears after a short delay
5. Use keyboard to navigate (if implemented)

#### Test 5.2: Loading States

1. Submit a form
2. **Expected Result**:
   - Button shows "Generating..." text
   - Button is disabled during loading
   - Loading indicator visible

#### Test 5.3: Responsive Design

1. Resize browser window
2. **Expected Result**: Layout adjusts appropriately
3. Test on mobile viewport
4. **Expected Result**: All elements remain usable

### 6. Performance Testing

#### Test 6.1: Caching

1. Search for "Chicago" in Current Location
2. Search for "Chicago" again in Pickup Location
3. **Expected Result**: Second search should be faster (cached)
4. Check Django console logs
5. **Expected Result**: Should see cache warnings but functionality works

#### Test 6.2: Multiple Rapid Searches

1. Type quickly in a location field, changing the text rapidly
2. **Expected Result**:
   - Only the latest search results appear
   - No race conditions or duplicate dropdowns

### 7. Map Display Testing

#### Test 7.1: Route Visualization

1. Generate a route
2. **Expected Result**:
   - Map displays with route line
   - Route follows actual roads (not straight line)
   - Multiple waypoints visible along the route

#### Test 7.2: Map Zoom and Pan

1. After route is displayed, try zooming in/out
2. Try panning the map
3. **Expected Result**: Map controls work smoothly

### 8. Data Validation Testing

#### Test 8.1: Required Fields

1. Try to submit form with empty location fields
2. **Expected Result**: Browser validation prevents submission

#### Test 8.2: Numeric Validation

1. Try entering negative numbers in "Current Cycle Hours"
2. **Expected Result**: Field doesn't accept negative values
3. Try entering text
4. **Expected Result**: Field only accepts numbers

## Known Issues and Limitations

1. **Cache Key Warnings**: Django cache shows warnings about special characters in keys (commas, spaces). This is cosmetic and doesn't affect functionality.

2. **OSRM Coverage**: OSRM routing works best for locations with good road data. Some remote areas might fall back to geodesic distance.

3. **Rate Limiting**: Nominatim has a 1 request/second limit. Rapid searches are throttled.

4. **CORS**: Frontend must run on localhost:3000 and backend on 127.0.0.1:8000 for proper CORS handling.

## Success Criteria

✅ All location fields show autocomplete suggestions
✅ Suggestions can be selected and populate the form
✅ Form submission generates routes with realistic distances
✅ Map displays routes following actual roads
✅ Error handling works gracefully
✅ Performance is acceptable (< 3 seconds for route generation)
✅ UI is responsive and user-friendly

## Troubleshooting

### Autocomplete not working

- Check browser console for errors
- Verify backend is running on http://127.0.0.1:8000
- Check network tab to see if API calls are being made

### Route generation fails

- Check Django console for errors
- Verify locations are being geocoded successfully
- Check if OSRM service is accessible

### Map not displaying

- Check if route_coordinates are in the response
- Verify MapView component is receiving data
- Check browser console for JavaScript errors
