from fastapi import APIRouter

from app.api.endpoint.auth import auth_router
from app.api.endpoint.term import term_router
from app.api.endpoint.analysis import analysis_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(term_router)
router.include_router(analysis_router)
