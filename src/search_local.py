"""
Min-conflicts local search algorithm for CSP solving.
Implements iterative improvement starting from a complete random assignment.
"""

import random
import time
from typing import Any, Dict, Optional
from core import CSP


class LocalSearchStatistics:
    """Track local search statistics."""
    
    def __init__(self):
        self.steps = 0
        self.conflict_checks = 0
        self.start_time = None
        self.end_time = None
    
    def reset(self):
        """Reset all counters."""
        self.steps = 0
        self.conflict_checks = 0
        self.start_time = None
        self.end_time = None
    
    def runtime(self) -> float:
        """Get runtime in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def __str__(self):
        return (f"Steps: {self.steps}, "
                f"Conflict Checks: {self.conflict_checks}, "
                f"Runtime: {self.runtime():.4f}s")


local_stats = LocalSearchStatistics()


def min_conflicts(csp: CSP, max_steps: int = 10000) -> Optional[Dict[Any, Any]]:
    """
    Solve a CSP using min-conflicts local search.
    
    Starts with a complete random assignment and iteratively improves it
    by selecting conflicted variables and assigning values that minimize conflicts.
    
    Args:
        csp: The constraint satisfaction problem to solve
        max_steps: Maximum number of iterations before giving up
        
    Returns:
        Complete assignment if solution found, None otherwise
    """
    local_stats.reset()
    local_stats.start_time = time.time()
    
    assignment = {}
    for var in csp.variables:
        assignment[var] = random.choice(list(csp.domains[var]))
    
    for step in range(max_steps):
        local_stats.steps += 1
        
        conflicted = get_conflicted_variables(csp, assignment)
        
        if not conflicted:
            local_stats.end_time = time.time()
            return assignment
        
        var = random.choice(conflicted)
        
        best_value = get_min_conflict_value(csp, var, assignment)
        
        assignment[var] = best_value
    
    local_stats.end_time = time.time()
    return None


def get_conflicted_variables(csp: CSP, assignment: Dict[Any, Any]) -> list:
    """
    Find all variables that are involved in constraint violations.
    
    Args:
        csp: The constraint satisfaction problem
        assignment: Current complete assignment
        
    Returns:
        List of variables that have conflicts
    """
    conflicted = []
    
    for var in csp.variables:
        has_conflict = False
        for constraint in csp.constraints[var]:
            local_stats.conflict_checks += 1
            if not constraint.is_satisfied(assignment):
                has_conflict = True
                break
        
        if has_conflict:
            conflicted.append(var)
    
    return conflicted


def get_min_conflict_value(csp: CSP, var: Any, assignment: Dict[Any, Any]) -> Any:
    """
    Find the value for var that minimizes the number of conflicts.
    
    Args:
        csp: The constraint satisfaction problem
        var: The variable to assign
        assignment: Current complete assignment
        
    Returns:
        Value that minimizes conflicts (ties broken randomly)
    """
    conflict_counts = {}
    
    for value in csp.domains[var]:
        old_value = assignment[var]
        assignment[var] = value
        
        conflicts = 0
        for constraint in csp.constraints[var]:
            local_stats.conflict_checks += 1
            if not constraint.is_satisfied(assignment):
                conflicts += 1
        
        conflict_counts[value] = conflicts
        
        assignment[var] = old_value
    
    min_conflicts = min(conflict_counts.values())
    
    best_values = [value for value, count in conflict_counts.items() 
                   if count == min_conflicts]
    
    return random.choice(best_values)


def get_local_statistics() -> LocalSearchStatistics:
    """
    Get the current local search statistics.
    
    Returns:
        LocalSearchStatistics object with counters and timing information
    """
    return local_stats
