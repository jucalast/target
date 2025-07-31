# API Documentation

This document provides comprehensive documentation for the Market Analysis API, which processes market data from various sources including IBGE and Google Trends.

## Base URL

``` 
https://api.marketanalysis.example.com/v1
```

## Authentication

All endpoints require API key authentication. Include your API key in the `X-API-Key` header.

```
X-API-Key: your_api_key_here
```

## Endpoints

### 1. Analyze Market

Analyze a market niche using natural language processing and external data sources.

**Endpoint:** `POST /analyze`

#### Request Body

```json
{
  "niche": "Tecnologia",
  "description": "Análise do mercado de tecnologia no Brasil",
  "options": {
    "include_google_trends": true,
    "ibge_tables": ["6401", "7482"],
    "timeframe": "last_12_months"
  }
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `niche` | string | Yes | The market niche to analyze |
| `description` | string | Yes | Detailed description of the analysis |
| `options.include_google_trends` | boolean | No | Include Google Trends data (default: true) |
| `options.ibge_tables` | string[] | No | Specific IBGE tables to include |
| `options.timeframe` | string | No | Time period for the analysis |

#### Response

```json
{
  "analysis_id": "anal_abc123",
  "status": "processing",
  "created_at": "2023-01-01T12:00:00Z",
  "links": {
    "self": "/v1/analyze/anal_abc123",
    "status": "/v1/analyze/anal_abc123/status"
  }
}
```

### 2. Get Analysis Status

Check the status of a previously requested analysis.

**Endpoint:** `GET /analyze/{analysis_id}/status`

#### Response

```json
{
  "analysis_id": "anal_abc123",
  "status": "completed",
  "progress": 100,
  "created_at": "2023-01-01T12:00:00Z",
  "completed_at": "2023-01-01T12:01:30Z",
  "result": {
    "url": "/v1/analyze/anal_abc123/result"
  }
}
```

### 3. Get Analysis Result

Retrieve the results of a completed analysis.

**Endpoint:** `GET /analyze/{analysis_id}/result`

#### Response

```json
{
  "analysis_id": "anal_abc123",
  "status": "completed",
  "created_at": "2023-01-01T12:00:00Z",
  "processing_time": 90.5,
  "input": {
    "niche": "Tecnologia",
    "description": "Análise do mercado de tecnologia no Brasil"
  },
  "nlp": {
    "keywords": [
      {"keyword": "tecnologia", "score": 0.95, "source": "tfidf"},
      {"keyword": "inovação", "score": 0.87, "source": "tfidf"}
    ],
    "topics": [
      {
        "label": "Tecnologia e Inovação",
        "weight": 0.92,
        "keywords": [
          {"keyword": "tecnologia", "score": 0.98},
          {"keyword": "inovação", "score": 0.95}
        ]
      }
    ]
  },
  "ibge": {
    "6401": {
      "table_name": "PNAD Contínua",
      "period": "2023-01/2023-12",
      "data": [{"variable": "Rendimento médio", "value": 2500.0}]
    }
  },
  "google_trends": {
    "interest_over_time": [
      {"date": "2023-01-01", "value": 75, "keyword": "tecnologia"}
    ]
  },
  "insights": {
    "market_size": "large",
    "growth_potential": "high",
    "key_opportunities": ["AI", "Cloud Computing"]
  }
}
```

## Data Models

### Analysis Request

```typescript
interface AnalysisRequest {
  niche: string;
  description: string;
  options?: {
    include_google_trends?: boolean;
    ibge_tables?: string[];
    timeframe?: 'last_month' | 'last_3_months' | 'last_12_months' | 'all';
  };
}
```

### Analysis Response

```typescript
interface AnalysisResponse {
  analysis_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;  // ISO 8601 datetime
  processing_time?: number;  // in seconds
  input: {
    niche: string;
    description: string;
  };
  nlp: {
    keywords: Array<{
      keyword: string;
      score: number;
      source?: string;
    }>;
    topics: Array<{
      label: string;
      weight: number;
      keywords: Array<{
        keyword: string;
        score: number;
      }>;
    }>;
  };
  ibge: Record<string, {
    table_name: string;
    period: string;
    data: Array<Record<string, any>>;
  }>;
  google_trends?: {
    interest_over_time: Array<{
      date: string;
      value: number;
      keyword: string;
    }>;
    related_queries?: Record<string, {
      top: Array<{query: string; value: number}>;
      rising: Array<{query: string; value: number}>;
    }>;
  };
  insights: Record<string, any>;
}
```

## Error Handling

All error responses follow this format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {
      "field_name": "Additional error details"
    }
  }
}
```

### Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `invalid_request` | The request is missing required parameters | 400 |
| `unauthorized` | Invalid or missing API key | 401 |
| `not_found` | The requested resource was not found | 404 |
| `rate_limit_exceeded` | API rate limit exceeded | 429 |
| `internal_error` | Internal server error | 500 |

## Rate Limiting

- **Free Plan:** 100 requests/hour
- **Pro Plan:** 1,000 requests/hour
- **Enterprise:** Custom limits

Exceeded limits will return a `429 Too Many Requests` response with a `Retry-After` header.

## Changelog

### v1.0.0 (2023-01-01)
- Initial release of the Market Analysis API
- Support for IBGE and Google Trends integration
- Basic NLP analysis capabilities

## Support

For support, please contact [support@marketanalysis.example.com](mailto:support@marketanalysis.example.com).
