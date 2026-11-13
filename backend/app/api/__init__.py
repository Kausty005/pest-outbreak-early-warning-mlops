from .advisory import router as advisory_router
from .crop import router as crop_router
from .farm_zones import router as farm_router
from .fertilizer import router as fertilizer_router
from .lifecycle import router as lifecycle_router
from .monitoring import router as monitoring_router
from .pest_risk import router as pest_risk_router
from .pest_surveillance import router as pest_surveillance_router
from .public_advisories import router as public_advisories_router

__all__ = [
    "advisory_router",
    "crop_router",
    "farm_router",
    "fertilizer_router",
    "lifecycle_router",
    "monitoring_router",
    "pest_risk_router",
    "pest_surveillance_router",
    "public_advisories_router",
]
