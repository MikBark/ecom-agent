import grpc
from grpc_health.v1 import health_pb2

from ecom_agent.health import build_health_servicer, mark_serving, register_health_service


def test_register_and_mark_serving() -> None:
    server = grpc.aio.server()
    servicer = build_health_servicer()

    register_health_service(server, servicer)
    mark_serving(servicer, "ecom_agent.v1.AgentService")

    status = servicer._server_status["ecom_agent.v1.AgentService"]
    assert status == health_pb2.HealthCheckResponse.SERVING
