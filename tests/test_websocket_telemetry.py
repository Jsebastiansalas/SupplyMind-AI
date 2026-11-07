"""
tests/test_websocket_telemetry.py
Pruebas para el canal WebSocket de telemetría en vivo de la jornada desatendida.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app
from tools.batch_processor.telemetry_ws import telemetry_broadcaster

client = TestClient(app)


def test_websocket_telemetry_connect_and_ping():
    with client.websocket_connect("/api/batch/ws/telemetry") as ws:
        # 1. Al conectar recibe el INIT_STATE
        init_msg = ws.receive_json()
        assert init_msg["type"] == "INIT_STATE"
        assert "data" in init_msg
        data = init_msg["data"]
        assert "status" in data
        assert "total_units" in data

        # 2. Enviar ping y recibir PONG
        ws.send_text("ping")
        pong_msg = ws.receive_json()
        assert pong_msg["type"] == "PONG"
        assert pong_msg["data"]["status"] == "alive"

        # 3. Solicitar heartbeat manual
        ws.send_text("heartbeat")
        hb_msg = ws.receive_json()
        assert hb_msg["type"] == "HEARTBEAT"
        assert "status" in hb_msg["data"]


def test_websocket_telemetry_broadcast():
    with client.websocket_connect("/api/batch/ws/telemetry") as ws:
        # Descartar INIT_STATE
        _ = ws.receive_json()

        # Enviar broadcast desde backend
        test_payload = {
            "task_id": "TEST_UNIT_9999",
            "status": "SUCCESS",
            "tokens": 450,
            "claimable_amount": 12500.00
        }
        telemetry_broadcaster.broadcast_sync("CASE_PROCESSED", test_payload)

        # Verificar que el cliente WebSocket lo recibe
        event = ws.receive_json()
        assert event["type"] in ["CASE_PROCESSED", "HEARTBEAT"]
        if event["type"] == "CASE_PROCESSED":
            assert event["data"]["task_id"] == "TEST_UNIT_9999"
            assert event["data"]["status"] == "SUCCESS"
