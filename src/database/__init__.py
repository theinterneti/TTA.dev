"""
Database module for the TTA.dev framework.

This module provides database integration components.
"""

from .neo4j_manager import Neo4jManager, get_neo4j_manager

__all__ = ["Neo4jManager", "get_neo4j_manager"]
