from .crop import router as crop_router
from .fertilizer import router as fertilizer_router
from .advisory import router as advisory_router
from .monitoring import router as monitoring_router
from .farm_zones import router as farm_router
from .pest_risk import router as pest_risk_router
from .public_advisories import router as public_advisories_router
from .pest_surveillance import router as pest_surveillance_router

__all__ = [
    "crop_router",
    "fertilizer_router",
    "advisory_router",
    "monitoring_router",
    "farm_router",
    "pest_risk_router",
    "public_advisories_router",
    "pest_surveillance_router",
]
