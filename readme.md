# KMB Yu Chui Court ETA Display

A real-time bus arrival time display service designed for KMB stops at Yu Chui Court. Features a modern transit-style display board with automatic updates, similar to those found in transit stations.

## Features

- Real-time ETA updates every 15 seconds
- Modern 5-column transit display layout
- Automatic route direction grouping
- Visual indicators for arriving buses
- Full-screen display optimized for large monitors
- Blinking effect for imminent arrivals
- Bilingual support (English/Chinese)

## Prerequisites

- Python 3.8+
- Flask
- Requests

## Quick Start

1. Install required packages:
```bash
pip install flask requests
```

2. Start the server:
```bash
python kmb_eta_server.py
```

3. Open `http://localhost:5000` in your browser

## Project Structure

```
project/
├── kmb_eta_server.py    # Main Flask application & API endpoints
├── templates/
│   └── index.html       # Frontend display template & styling
└── README.md
```

## API Documentation

### Get Yu Chui Court Stops
```
GET /api/stops
```
Returns list of KMB bus stops at Yu Chui Court

Response format:
```json
[
  {
    "stop": "string",
    "name_en": "string",
    "name_tc": "string",
    "lat": "string",
    "long": "string"
  }
]
```

### Get Stop ETAs
```
GET /api/eta/<stop_id>
```
Returns ETA data for specified stop ID

Response format:
```json
{
  "etas": [
    {
      "route": "string",
      "eta": "datetime",
      "dest_tc": "string",
      "dest_en": "string"
    }
  ],
  "updated_at": "datetime"
}
```

## Data Source

Uses KMB's open data API:
- Stop Data: `https://data.etabus.gov.hk/v1/transport/kmb/stop`
- ETA Data: `https://data.etabus.gov.hk/v1/transport/kmb/stop-eta/{stop_id}`

## Technical Details

### Backend (`kmb_eta_server.py`)
- Flask-based web server
- Automatic data caching
- Background thread for ETA updates
- Error handling for API failures
- Configurable update interval (15s default)

### Frontend (`templates/index.html`)
- Modern transit display design
- CSS Grid for 5-column layout
- Real-time updates via JavaScript
- Responsive text sizing
- Clean typography with Courier New font
- Professional color scheme:
  - Route numbers: Golden yellow (#ffd700)
  - ETAs: Bright green (#39ff14)
  - Destinations: White
  - Background: Black

## Error Handling

- Graceful handling of API failures
- Automatic retry on connection errors
- Clear error messages for users
- Continued operation with cached data when API is unavailable

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Acknowledgments

- KMB Open Data API
- Flask framework
- Bootstrap CSS