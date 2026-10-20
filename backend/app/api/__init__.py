from .crop import router as crop_router
from .fertilizer import router as fertilizer_router
from .advisory import router as advisory_router
from .monitoring import router as monitoring_router

__all__ = ["crop_router", "fertilizer_router", "advisory_router", "monitoring_router"]

