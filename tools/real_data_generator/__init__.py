"""
Paquete Generador de Datos Comerciales Reales y Topología B2B Auténtica (Sprint 3.1).
"""

from tools.real_data_generator.retailer_catalog import (
    RETAILER_CATALOG,
    BuyerEnterpriseProfile,
    DeductionPolicy,
    RetailerContractClause,
    ProductItemTemplate,
    DEFAULT_SUPPLIER_PROFILE,
    get_retailer_profile,
    list_available_retailers,
    find_deduction_policy
)
from tools.real_data_generator.case_synthesizer import (
    CaseDossier,
    EnterpriseCaseSynthesizer
)

__all__ = [
    "RETAILER_CATALOG",
    "BuyerEnterpriseProfile",
    "DeductionPolicy",
    "RetailerContractClause",
    "ProductItemTemplate",
    "DEFAULT_SUPPLIER_PROFILE",
    "get_retailer_profile",
    "list_available_retailers",
    "find_deduction_policy",
    "CaseDossier",
    "EnterpriseCaseSynthesizer"
]
