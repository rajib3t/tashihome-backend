from fastapi import FastAPI, HTTPException, Request
from contextlib import asynccontextmanager

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import db 

from app.core.exceptions import AppException
from app.core.logging_config import configure_logging
from app.core.redis import redis_client
from app.core.leader_election import RedisLeaderElector
from app.events.subscriber import start_event_subscriber
import asyncio
import logging
from app.api.router import api_router
import uvicorn
class Application:
    def __init__(self):
       
       self.app = FastAPI(
           lifespan=self.lifespan,
           title=settings.APP_NAME,
       )

       self._register_middleware()
       self._register_exception_handlers()
       self._register_routes()
   

    @staticmethod
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger = logging.getLogger(__name__)
        # Connect the module-level `db` so dependencies share the same session factory.
        db.connect()
        app.state.db = db

        try:
            await redis_client.connect()
            app.state.redis = redis_client
            app.state.redis_event_subscriber_task = asyncio.create_task(start_event_subscriber())
            leader_elector = RedisLeaderElector()
            await leader_elector.start(start_event_subscriber)
            app.state.leader_elector = leader_elector
        except Exception:
            logger.warning("Redis connection could not be established at startup")


        yield


        if hasattr(app.state, "redis_event_subscriber_task") and app.state.redis_event_subscriber_task is not None:
            task = app.state.redis_event_subscriber_task
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if hasattr(app.state, "leader_elector") and app.state.leader_elector is not None:
            await app.state.leader_elector.stop()

        if hasattr(app.state, "db") and app.state.db is not None:
            await app.state.db.disconnect()
            logger.info("Database connection closed")

        if hasattr(app.state, "redis") and app.state.redis is not None:
            await app.state.redis.close()
            logger.info("Redis connection closed")

    
    def _register_middleware(self):
        # Register TrustedHostMiddleware using parsed allowed hosts from settings
        try:
            from starlette.middleware.trustedhost import TrustedHostMiddleware
            hosts = settings.allowed_hosts
            if hosts:
                self.app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)
        except Exception:
            # If middleware cannot be registered, continue without crashing startup
            pass
        # Register CORS middleware
        try:
            from fastapi.middleware.cors import CORSMiddleware
            cors_origins = settings.cors_allowed_origins
            # In development, allow all origins if none configured
            if not cors_origins and getattr(settings, "DEBUG", False):
                cors_origins = ["*"]
            if cors_origins:
                self.app.add_middleware(
                    CORSMiddleware,
                    allow_origins=cors_origins,
                    allow_credentials=True,
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
        except Exception:
            pass

    def _register_exception_handlers(self):
        logger = logging.getLogger(__name__)
        @self.app.exception_handler(AppException)
        async def app_exception_handler(request: Request, exc: AppException):
            logger.error(f"AppException: {exc.status_code} - {exc.message}")
            if isinstance(exc.detail, dict):
                return JSONResponse(
                    status_code=exc.status_code,
                    content=exc.detail
                )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "status": "error",
                    "message": exc.detail
                }
            )

        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            logger = logging.getLogger(__name__)
            errors = []
            for err in exc.errors():
                field = err["loc"][-1]
                message = err["msg"]
                errors.append({
                    "field": field,
                    "message": message
                })
            logger.error(f"Validation error: {errors}")
            return JSONResponse(
                status_code=422,
                content={
                    "status": "error",
                    "message": "Validation error",
                    "errors": errors
                },
            )

        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            logger.error(f"HTTPException: {exc.status_code} - {exc.detail}")
            message = exc.detail
            if isinstance(message, dict):
                return JSONResponse(
                    status_code=exc.status_code,
                    content=message
                )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "status": "error",
                    "message": message,
                }
            )

    def _register_routes(self):
        self.app.get("/", tags=["Health"])(self._root)
        self.app.include_router(api_router)

    async def _root(self):
        return {"status": "ok", "message": "Service is running"}

    def get_app(self) -> FastAPI:
        return self.app 


configure_logging()

application = Application()
app = application.get_app() 


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
    )
