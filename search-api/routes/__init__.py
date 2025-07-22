from .search_routes import router as search_router
from .autocomplete_routes import router as autocomplete_router
from .analytics_routes import router as analytics_router
from .health_routes import router as health_router

__all__ = [
    "search_router",
    "autocomplete_router", 
    "analytics_router",
    "health_router"
]