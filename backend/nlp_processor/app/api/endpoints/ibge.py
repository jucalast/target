"""
Endpoints para consulta de dados do IBGE.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from shared.db.database import get_db
from shared.schemas.ibge import (
    IBEResult,
    IBGEQueryBase,
    IBGEDemographicQuery,
    IBGEDemographicResult
)

# Import the actual implementation from etl_pipeline
from etl_pipeline.app.services.api.endpoints.ibge import router as ibge_router

# Create a new router for the nlp_processor module
router = APIRouter()

# Include all routes from the etl_pipeline's ibge router
router.include_router(
    ibge_router,
    prefix="",
    tags=["IBGE Data"]
)

# You can add any additional endpoints specific to the nlp_processor module here
# For example, endpoints that combine NLP processing with IBGE data
