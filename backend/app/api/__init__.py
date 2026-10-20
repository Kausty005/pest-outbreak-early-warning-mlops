from .crop import router as crop_router
from .fertilizer import router as fertilizer_router
from .advisory import router as advisory_router
from .monitoring import router as monitoring_router
from .pest import router as pest_router
from .pest_forecast import router as pest_forecast_router

__all__ = [
    "crop_router",
    "fertilizer_router",
    "advisory_router",
    "monitoring_router",
    "pest_router",
    "pest_forecast_router",
]

