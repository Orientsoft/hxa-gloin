from fastapi import APIRouter

from app.api.user import router as user_router
from app.api.case import router as case_router
from app.api.count import router as count_router
from app.api.analysis import router as analysis_router

router = APIRouter()
'''
example:
    router.include_router(xxx, tags=["xxx"], prefix="/xxx")
'''

router.include_router(user_router)
router.include_router(case_router)
router.include_router(count_router)
router.include_router(analysis_router)
