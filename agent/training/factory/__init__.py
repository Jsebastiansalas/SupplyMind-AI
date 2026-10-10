"""
Módulo Fábrica Adversarial de Disputas B2B (Adversarial Dispute Factory).

Provee los generadores de expedientes comerciales sintéticos, agentes adversariales
con intereses contrapuestos (Comprador Retailer, Transportista y Abogado) y
los esquemas de Ground Truth determinísticos para entrenamiento y evaluación colegiada.
"""

from agent.training.factory.ground_truth import (
    DiscrepancyCategory,
    CommercialActionType,
    GroundTruthLineItem,
    GroundTruthDeductionAssessment,
    GroundTruthDeduction,
    GroundTruth,
)
from agent.training.factory.retailer_agent import RetailerBuyerAgent
from agent.training.factory.carrier_agent import CarrierLogisticsAgent
from agent.training.factory.lawyer_agent import CorporateLawyerAgent
from agent.training.factory.case_synthesizer import AdversarialCaseSynthesizer

__all__ = [
    "DiscrepancyCategory",
    "CommercialActionType",
    "GroundTruthLineItem",
    "GroundTruthDeductionAssessment",
    "GroundTruthDeduction",
    "GroundTruth",
    "RetailerBuyerAgent",
    "CarrierLogisticsAgent",
    "CorporateLawyerAgent",
    "AdversarialCaseSynthesizer",
]
