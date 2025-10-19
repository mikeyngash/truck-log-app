# Truck Log App - HOS Compliance System

A professional truck driver log book application that generates compliant Hours of Service (HOS) logs with interactive maps and PDF exports.

## Live Demo

**Frontend:** https://www.albytechs.online  
**Backend API:** https://app-production-6389.up.railway.app

## Features

### Core Functionality

- **Route Planning** - Calculate optimal routes between locations
- **HOS Compliance** - Enforces 70hrs/8days rule automatically
- **Interactive Map** - Visual route display with Leaflet
- **PDF Generation** - Professional log sheets matching DOT standards
- **Sleeper Berth Support** - Split sleeper berth provision (8/2 split)
- **Smart Stops** - Automatic fueling stops every 1000 miles
- **Entry Merging** - Adjacent entries of same status are merged

### Technical Highlights

- Real-time route calculation using OSRM
- Geocoding with Nominatim
- RESTful API with Django REST Framework
- Responsive React frontend
- Production-ready deployment

## Architecture

```
truck-log-app/
├── backend/              # Django REST API
│   ├── core/            # Main application
│   │   ├── models.py    # Trip & LogEntry models
│   │   ├── services.py  # Business logic & HOS rules
│   │   ├── routing.py   # OSRM integration
│   │   ├── geocoding.py # Location services
│   │   └── views.py     # API endpoints
│   └── trucklog/        # Django settings
├── frontend/            # React application
│   └── src/
│       ├── components/  # React components
│       │   ├── TripForm.jsx
│       │   ├── MapView.jsx
│       │   ├── ResultPanel.jsx
│       │   └── LogGridSvg.jsx
│       └── App.js       # Main app
└── docs/               # Documentation
```

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 14+
- npm or yarn

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs at: `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Frontend runs at: `http://localhost:3000`

## API Endpoints

### Create Trip

```bash
POST /api/trip/
Content-Type: application/json

{
  "current_location": "Nairobi, Kenya",
  "pickup_location": "Machakos, Kenya",
  "dropoff_location": "Eldoret, Kenya",
  "current_cycle_hours": 5,
  "use_sleeper_berth": false
}
```

### Response

```json
{
  "trip_id": 1,
  "total_distance": 288.3,
  "total_time": 10.5,
  "logs": [...],
  "route_coordinates": [...],
  "pdf_url": "/media/logs/2025-10-18.pdf"
}
```

## HOS Rules Implemented

### 70-Hour/8-Day Rule

- Maximum 70 hours on-duty in any 8 consecutive days
- Automatically calculates remaining hours
- Prevents violations before they occur

### 11-Hour Driving Limit

- Maximum 11 hours of driving per day
- Enforced after 10 consecutive hours off-duty

### 14-Hour Driving Window

- All driving must occur within 14 hours of coming on-duty
- Cannot be extended with off-duty time

### 30-Minute Break

- Required after 8 hours of driving
- Must be at least 30 minutes off-duty

### Sleeper Berth Provision

- Split sleeper berth: 8 hours + 2 hours
- Pauses 14-hour clock
- Optional feature

## Testing

### Run Backend Tests

```bash
cd backend
python manage.py test
```

### Test API with cURL

```bash
curl -X POST http://localhost:8000/api/trip/ \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": "Nairobi, Kenya",
    "pickup_location": "Machakos, Kenya",
    "dropoff_location": "Eldoret, Kenya",
    "current_cycle_hours": 5
  }'
```

## Deployment

### Backend (Railway)

```bash
cd backend
railway login
railway init
railway up
railway domain
```

### Frontend (Vercel)

```bash
cd frontend
vercel login
vercel --prod
```

## Documentation

- [Implementation Summary](IMPLEMENTATION_SUMMARY.md)
- [Testing Guide](TESTING_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Quick Deploy](QUICK_DEPLOY.md)

## Tech Stack

### Backend

- Django 5.2
- Django REST Framework 3.16
- ReportLab (PDF generation)
- Geopy (Geocoding)
- Requests (HTTP client)

### Frontend

- React 18
- Axios (API client)
- Leaflet (Maps)
- React-Leaflet (React bindings)

### Deployment

- Railway (Backend)
- Vercel (Frontend)
- PostgreSQL (Production DB)

## License

MIT License - feel free to use this project for learning or commercial purposes.

## Author

Michael Nganga  
Email: michaelnganga552@gmail.com

## Acknowledgments

- FMCSA for HOS regulations documentation
- OSRM for routing services
- OpenStreetMap for map data
- Nominatim for geocoding services

## Support

For issues or questions:

1. Check the [documentation](IMPLEMENTATION_SUMMARY.md)
2. Review [testing guide](TESTING_GUIDE.md)
3. Open an issue on GitHub

---

**Built with care for truck drivers and fleet managers**
