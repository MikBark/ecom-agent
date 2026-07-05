import grpc
from grpc_health.v1 import health, health_pb2, health_pb2_grpc


def build_health_servicer() -> health.HealthServicer:
    return health.HealthServicer()


def register_health_service(server: grpc.aio.Server, servicer: health.HealthServicer) -> None:
    health_pb2_grpc.add_HealthServicer_to_server(servicer, server)


def mark_serving(servicer: health.HealthServicer, service_name: str) -> None:
    servicer.set(service_name, health_pb2.HealthCheckResponse.SERVING)
