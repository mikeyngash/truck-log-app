# Truck Log App Improvements TODO

## Backend Improvements (High Priority)

- [x] Enhance HOS Logic: Implement rolling 70-hour/8-day calculation with historical data simulation
  - [x] Initialize rolling 8-day window with simulated historical on-duty hours based on current_cycle_hours
  - [x] Update accumulation logic to track daily on-duty hours and maintain rolling total
  - [x] Implement compliance checks using rolling total and force breaks if exceeding 70 hours
  - [x] Update HOS validation section to use new rolling calculation
- [x] Add Sleeper Berth Support: Optional input for split breaks (7+ hours in berth + 2+ hours off-duty)
- [x] Refine 14-Hour Window: Start window after 10 consecutive off-duty hours, prevent extensions beyond 14 hours
- [ ] Handle Edge Cases: Short-haul exceptions, personal conveyance, adverse conditions extension
- [ ] Realistic Fueling: Insert stops every 500-1000 miles at logical points
- [x] Integrate Real Geocoding: Use Nominatim for dynamic location coordinates
- [ ] Add Routing API: Use OSRM for actual paths and waypoints
- [ ] Precise Log Generation: Use Pillow/ReportLab for accurate grid drawing, PDF output
- [ ] Add Validation: Check for HOS violations, suggest trip splits
- [ ] Unit Tests: Add Django tests for HOS scenarios
- [ ] Security: Add input sanitization, API authentication, HTTPS
- [ ] Performance: Cache geopy calls, optimize database queries

## Frontend Improvements (High Priority)

- [ ] Map Enhancements: Integrate leaflet-routing-machine for curved routes, dynamic markers, animations
- [ ] Form Improvements: Add autocomplete for locations, better error feedback
- [ ] Results Display: Make logs zoomable, add download buttons for PDF
- [ ] Animations: Use Framer Motion for fade-ins and futuristic effects
- [ ] Responsiveness: Ensure mobile compatibility with media queries
- [ ] State Management: Implement Redux/Context for better handling of multiple trips
- [x] Loading States: Add loading indicators for map and logs
- [x] Accessibility: Add ARIA labels, keyboard navigation, screen reader support
- [ ] Performance: Lazy-load components, optimize bundle size

## Overall Project

- [ ] Testing and Validation: Manual validation against FMCSA examples, edge case testing
- [ ] Deployment: Prepare for production deployment
