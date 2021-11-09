from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import uvicorn

from app.core.errors import http_error_handler, http422_error_handler, catch_exceptions_middleware
from app.api import router as api_router
from app.core.config import allowed_hosts, prefix_url, debug, version, host, port, project_name
from app.db.mongodb import connect_to_mongodb, close_mongo_connection
from app.utils.utils import scan_files_by_path

app = FastAPI(title=project_name, debug=debug, version=version)

# 普通异常全局捕获
app.middleware('http')(catch_exceptions_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = AsyncIOScheduler()

app.add_event_handler("startup", connect_to_mongodb)
app.add_event_handler("shutdown", close_mongo_connection)

app.add_exception_handler(HTTPException, http_error_handler)
app.add_exception_handler(RequestValidationError, http422_error_handler)

app.include_router(api_router, prefix=prefix_url)


@app.on_event('startup')
def init_scheduler():
    scheduler.add_job(func=scan_files_by_path, trigger='interval', minutes=10, next_run_time=datetime.now())
    scheduler.start()


if __name__ == '__main__':
    uvicorn.run(
        app="app.main:app",
        host=host,
        port=port,
        reload=True,
        workers=1
    )
