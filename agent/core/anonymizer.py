import re
from typing import Dict, Any, List

class DataAnonymizer:
    """
    Middleware de ciberseguridad para ofuscar y restaurar datos sensibles
    antes de enviarlos al LLM (Grok/OpenAI) y al recibir su respuesta.
    """
    def __init__(self):
        # Mapeo bidireccional de datos sensibles
        self.sensitive_to_masked: Dict[str, str] = {
            "RetailCorp": "[CLIENTE_1]",
            "MegaMarket": "[CLIENTE_2]",
            "SuperTiendas": "[CLIENTE_3]",
            "Supermercados Éxito": "[CLIENTE_4]",
            "Acme Corp": "[PROVEEDOR_1]",
            "Global Suppliers": "[PROVEEDOR_2]",
        }
        self.masked_to_sensitive: Dict[str, str] = {
            v: k for k, v in self.sensitive_to_masked.items()
        }

    def anonymize_text(self, text: str) -> str:
        """Enmascara datos sensibles en un bloque de texto."""
        if not text:
            return text
        for sensitive, masked in self.sensitive_to_masked.items():
            text = text.replace(sensitive, masked)
        return text

    def deanonymize_text(self, text: str) -> str:
        """Restaura los datos sensibles desde su forma enmascarada."""
        if not text:
            return text
        for masked, sensitive in self.masked_to_sensitive.items():
            text = text.replace(masked, sensitive)
        return text

    def anonymize_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Aplica anonimización a una lista de mensajes estilo OpenAI."""
        anonymized = []
        for msg in messages:
            new_msg = msg.copy()
            if "content" in new_msg and isinstance(new_msg["content"], str):
                new_msg["content"] = self.anonymize_text(new_msg["content"])
            anonymized.append(new_msg)
        return anonymized

    def deanonymize_tool_calls(self, tool_calls) -> None:
        """Restaura in-place los argumentos de las tool_calls que vienen enmascaradas."""
        if not tool_calls:
            return
        for tool_call in tool_calls:
            if hasattr(tool_call, "function") and hasattr(tool_call.function, "arguments"):
                tool_call.function.arguments = self.deanonymize_text(tool_call.function.arguments)
