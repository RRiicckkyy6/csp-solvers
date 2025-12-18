"""
Graph coloring problem generator.
Generates random graph coloring CSP instances.
"""

import random
from typing import List, Tuple
from core import CSP
from constraints import NotEqualConstraint


def random_graph_coloring(n: int, p: float, k: int) -> CSP:
    """
    Generate a random graph coloring CSP instance.
    
    Args:
        n: Number of vertices in the graph
        p: Edge probability (0.0 to 1.0) - probability that any two vertices are connected
        k: Number of colors available
        
    Returns:
        CSP instance representing the graph coloring problem
    """
    csp = CSP()
    
    colors = set(range(k))
    
    vertices = list(range(n))
    for vertex in vertices:
        csp.add_variable(vertex, colors)
    
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() < p:
                constraint = NotEqualConstraint(i, j)
                csp.add_constraint(constraint)
    
    return csp


def create_graph_coloring(edges: List[Tuple[int, int]], k: int) -> CSP:
    """
    Create a graph coloring CSP from a specified list of edges.
    
    Args:
        edges: List of tuples (v1, v2) representing edges in the graph
        k: Number of colors available
        
    Returns:
        CSP instance representing the graph coloring problem
    """
    csp = CSP()
    
    colors = set(range(k))
    
    vertices = set()
    for v1, v2 in edges:
        vertices.add(v1)
        vertices.add(v2)
    
    for vertex in sorted(vertices):
        csp.add_variable(vertex, colors)
    
    for v1, v2 in edges:
        constraint = NotEqualConstraint(v1, v2)
        csp.add_constraint(constraint)
    
    return csp
