"""AccuSync FastAPI Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="請求書作成システム - Invoice Management System",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では具体的なオリジンを指定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} is starting...")
    print(f"📝 Environment: {settings.ENVIRONMENT}")
    print(f"🗄️  Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'N/A'}")
    print(f"🤖 AI Provider: {settings.AI_PROVIDER}")

    # Initialize database
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時の処理"""
    print(f"👋 {settings.APP_NAME} is shutting down...")


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Import and include routers
from app.api.v1.endpoints import imports
from app.api.v1.endpoints import settings as settings_router
from app.api.v1.endpoints import orders
from app.api.v1.endpoints import mapping
from app.api.v1.endpoints import products
from app.api.v1.endpoints import pricing_rules
from app.api.v1.endpoints import customers

app.include_router(
    imports.router,
    prefix="/api/v1/imports",
    tags=["imports"]
)

app.include_router(
    settings_router.router,
    prefix="/api/v1/settings",
    tags=["settings"]
)

app.include_router(
    orders.router,
    prefix="/api/v1/orders",
    tags=["orders"]
)

app.include_router(
    mapping.router,
    prefix="/api/v1/mapping",
    tags=["mapping"]
)

app.include_router(
    products.router,
    prefix="/api/v1/products",
    tags=["products"]
)

app.include_router(
    pricing_rules.router,
    prefix="/api/v1/pricing-rules",
    tags=["pricing-rules"]
)

app.include_router(
    customers.router,
    prefix="/api/v1/customers",
    tags=["customers"]
)

# TODO: Add more routers when implemented
# from app.api.v1 import auth, orders, invoices, products, customers
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
# app.include_router(invoices.router, prefix="/api/v1/invoices", tags=["invoices"])
# app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
# app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )
