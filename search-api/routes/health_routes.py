from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from config import client
import time

router = APIRouter(tags=["health"])

@router.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint to verify OpenSearch connection and service status"""
    try:
        start_time = time.time()
        
        # Check OpenSearch connection
        opensearch_health = client.cluster.health()
        opensearch_response_time = round((time.time() - start_time) * 1000, 2)
        
        # Check if indices exist
        indices_status = {}
        for index_name in ["posts", "users", "comments"]:
            try:
                exists = client.indices.exists(index=index_name)
                if exists:
                    # Get basic index stats
                    stats = client.indices.stats(index=index_name)
                    doc_count = stats["indices"][index_name]["total"]["docs"]["count"]
                    indices_status[index_name] = {
                        "exists": True,
                        "document_count": doc_count,
                        "status": "healthy"
                    }
                else:
                    indices_status[index_name] = {
                        "exists": False,
                        "status": "missing"
                    }
            except Exception as e:
                indices_status[index_name] = {
                    "exists": False,
                    "status": "error",
                    "error": str(e)
                }
        
        # Determine overall health status
        opensearch_status = opensearch_health.get("status", "unknown")
        all_indices_healthy = all(
            idx.get("exists", False) and idx.get("status") == "healthy" 
            for idx in indices_status.values()
        )
        
        overall_status = "healthy" if (
            opensearch_status in ["green", "yellow"] and all_indices_healthy
        ) else "unhealthy"
        
        return {
            "status": overall_status,
            "timestamp": time.time(),
            "opensearch": {
                "status": opensearch_status,
                "cluster_name": opensearch_health.get("cluster_name"),
                "number_of_nodes": opensearch_health.get("number_of_nodes"),
                "response_time_ms": opensearch_response_time
            },
            "indices": indices_status,
            "service": {
                "name": "search-api",
                "version": "1.0.0",
                "uptime": "running"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )

@router.get("/health/simple")
async def simple_health_check():
    """Simple health check that returns basic status"""
    try:
        # Quick OpenSearch ping
        client.cluster.health()
        return {"status": "ok", "timestamp": time.time()}
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "error"})

@router.get("/health/detailed", response_model=Dict[str, Any])
async def detailed_health_check():
    """Detailed health check with comprehensive system information"""
    try:
        start_time = time.time()
        
        # OpenSearch cluster info
        cluster_health = client.cluster.health()
        cluster_stats = client.cluster.stats()
        
        # Node information
        nodes_info = client.nodes.info()
        
        # Index statistics
        all_indices_stats = client.indices.stats()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "response_time_ms": response_time,
            "opensearch": {
                "cluster": {
                    "name": cluster_health.get("cluster_name"),
                    "status": cluster_health.get("status"),
                    "number_of_nodes": cluster_health.get("number_of_nodes"),
                    "number_of_data_nodes": cluster_health.get("number_of_data_nodes"),
                    "active_primary_shards": cluster_health.get("active_primary_shards"),
                    "active_shards": cluster_health.get("active_shards"),
                    "relocating_shards": cluster_health.get("relocating_shards"),
                    "initializing_shards": cluster_health.get("initializing_shards"),
                    "unassigned_shards": cluster_health.get("unassigned_shards")
                },
                "stats": {
                    "total_documents": cluster_stats.get("indices", {}).get("docs", {}).get("count", 0),
                    "total_size_bytes": cluster_stats.get("indices", {}).get("store", {}).get("size_in_bytes", 0)
                },
                "nodes": len(nodes_info.get("nodes", {}))
            },
            "indices": {
                index_name: {
                    "documents": stats.get("total", {}).get("docs", {}).get("count", 0),
                    "size_bytes": stats.get("total", {}).get("store", {}).get("size_in_bytes", 0),
                    "shards": {
                        "primary": stats.get("_shards", {}).get("successful", 0),
                        "total": stats.get("_shards", {}).get("total", 0)
                    }
                }
                for index_name, stats in all_indices_stats.get("indices", {}).items()
                if index_name in ["posts", "users", "comments"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )