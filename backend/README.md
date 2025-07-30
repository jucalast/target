# Market Analysis Backend

Backend service for analyzing market segments using NLP and public data sources like IBGE and Google Trends.

## Features

- **NLP Processing**: Extract keywords, topics, and entities from market descriptions
- **Data Integration**:
  - IBGE/SIDRA data (demographic, economic, and behavioral data)
  - Google Trends data (search interest and related queries)
- **ETL Pipeline**: Extract, transform, and load data from multiple sources
- **RESTful API**: Easy integration with frontend applications

## Tech Stack

- **Python 3.9+**
- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database interactions
- **spaCy & Transformers**: Natural language processing
- **scikit-learn**: Machine learning utilities (TF-IDF, LDA)
- **pandas**: Data manipulation
- **pytest**: Testing framework

## Project Structure

```
backend/
├── app/
│   ├── api/                  # API endpoints
│   ├── core/                 # Core configurations
│   ├── models/               # Database models
│   ├── schemas/             # Pydantic models for request/response
│   ├── services/            # Business logic and services
│   │   ├── nlp_service.py   # NLP processing
│   │   ├── sidra_mapper.py  # IBGE SIDRA integration
│   │   ├── google_trends_service.py  # Google Trends integration
│   │   └── etl_pipeline.py  # ETL orchestration
│   └── utils/               # Utility functions
├── tests/                   # Test files
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Getting Started

### Prerequisites

- Python 3.9 or higher
- PostgreSQL (or SQLite for development)
- Google Cloud account (for Google Trends API)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/market-analysis-backend.git
   cd market-analysis-backend/backend
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize the database**
   ```bash
   alembic upgrade head
   ```

### Running the Application

```bash
# Start the development server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit

# Run integration tests
pytest tests/integration

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

## API Documentation

Once the application is running, you can access:

- **Interactive API docs**: `http://localhost:8000/docs`
- **Alternative API docs**: `http://localhost:8000/redoc`
- **OpenAPI schema**: `http://localhost:8000/openapi.json`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection URL | `sqlite:///./sql_app.db` |
| `GOOGLE_TRENDS_EMAIL` | Google account email | - |
| `GOOGLE_TRENDS_PASSWORD` | Google account password | - |
| `ENVIRONMENT` | Runtime environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- IBGE for providing open data
- Google Trends for search interest data
- spaCy and Hugging Face for NLP models
