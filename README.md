# Water Quality Monitoring & Analytics System

A cloud-integrated IoT system for monitoring water quality with real-time analytics and dashboard visualization.

## System Architecture

```
Sensors → ESP32 → USB Serial → Python Bridge → Cloud API → Database → Dashboard
```

## Features

- **Real-time Data Ingestion**: Process water quality telemetry from ESP32 via serial communication
- **Data Enrichment**: Calculate TDS, WQI, and irrigation sustainability indices
- **Cloud Storage**: SQLAlchemy ORM with SQLite (easily upgradeable to PostgreSQL)
- **REST API**: FastAPI with endpoints for ingestion, history, and metrics
- **Modern Dashboard**: Responsive web interface with real-time charts and gauges
- **Resilient Design**: Retry logic, error handling, and local logging for failed uploads

## Quick Start

### Prerequisites

- Python 3.8+
- ESP32 with water quality sensors
- USB serial connection (COM11)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd water-quality-monitoring
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the API server:
```bash
cd app
python main.py
```

The API will be available at `http://localhost:8080`

4. Start the serial bridge (in a separate terminal):
```bash
cd bridge
python serial_bridge.py
```

### API Endpoints

- `GET /` - Dashboard UI
- `GET /health` - Health check
- `POST /api/ingest` - Ingest telemetry data
- `GET /api/latest` - Get latest reading
- `GET /api/history?limit=100` - Get historical data
- `GET /api/metrics` - Get aggregated metrics
- `GET /api/devices` - List device IDs

### Dashboard Features

- **Real-time Charts**: EC and temperature trends
- **WQI Gauge**: Visual water quality indicator
- **Metrics Cards**: Current readings and statistics
- **Irrigation Status**: Suitability assessment
- **Auto-refresh**: Updates every 30 seconds

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string (default: `sqlite:///./water_quality.db`)
- `API_URL`: Cloud API endpoint for bridge (default: `http://localhost:8000/api/ingest`)
- `SERIAL_PORT`: Serial port for ESP32 connection (default: `COM11`)

### Serial Data Format

The bridge expects ESP32 to output in this format:

```
BOOTED
TEMP: 30.44
EC: 1.023
FINAL
TEMP: 30.44
EC: 1.125
```

Only readings after the "FINAL" marker are processed.

## Data Enrichment

The system calculates:

- **TDS**: EC × 500 (ppm)
- **WQI**: Temperature and EC-based algorithm (placeholder)
- **Irrigation Index**:
  - EC < 0.7 → Excellent
  - 0.7–3.0 → Moderate  
  - > 3.0 → Unsuitable

## Testing

Run the test suite:

```bash
python test_system.py
```

This validates:
- API connectivity
- Data ingestion
- All endpoint functionality

## File Structure

```
water-quality-monitoring/
├── app/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database configuration
│   ├── routes.py            # API endpoints
│   ├── templates/
│   │   └── dashboard.html   # Dashboard UI
│   └── static/              # CSS/JS assets
├── bridge/
│   └── serial_bridge.py     # Serial communication bridge
├── requirements.txt         # Python dependencies
├── test_system.py          # Test suite
└── README.md               # This file
```

## Monitoring & Logging

- Structured logging for all operations
- Failed uploads logged locally (`failed_uploads.log`)
- API request/response logging
- Database operation tracking

## Security Features

- Input validation on all endpoints
- CORS configuration
- HTTPS support (via Render)
- SQL injection prevention via SQLAlchemy

## Scalability

- Easy database migration from SQLite to PostgreSQL
- Stateless API design for horizontal scaling
- Modular bridge architecture
- Cloud-native deployment ready

## Troubleshooting

### Common Issues

1. **Serial Connection Failed**
   - Check COM port number
   - Verify ESP32 is connected and powered
   - Ensure baud rate matches (115200)

2. **API Connection Refused**
   - Verify API server is running
   - Check firewall settings
   - Confirm port 8000 is available

3. **Dashboard Not Loading**
   - Check browser console for errors
   - Verify API endpoints are accessible
   - Ensure static files are served correctly

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
