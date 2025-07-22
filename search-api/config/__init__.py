# Configuration package
from .opensearch import client, INDICES_CONFIG, create_indices
from .settings import OPENSEARCH_HOST, OPENSEARCH_PORT

__all__ = [
    "client",
    "INDICES_CONFIG", 
    "create_indices",
    "OPENSEARCH_HOST",
    "OPENSEARCH_PORT"
]