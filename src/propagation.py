"""
Inference algorithms for CSP solving.
Implements domain reduction through constraint propagation.
"""

from typing import Any, Dict, List, Set, Tuple, Optional
from collections import deque
from core import CSP


def forward_checking(csp: CSP, var: Any, value: Any, domains: Dict[Any, Set[Any]]) -> Tuple[bool, Optional[Any]]:
    """
    Apply forward checking after assigning value to var.
    
    Removes inconsistent values from domains of unassigned neighbors.
    Only checks neighbors of the assigned variable (not full arc consistency).
    
    When a domain wipeout occurs, increments weights of constraints that caused it
    (for dom/wdeg heuristic).
    
    Args:
        csp: The constraint satisfaction problem
        var: The variable that was just assigned
        value: The value assigned to var
        domains: Current domains (modified in-place)
        
    Returns:
        Tuple of (success, culprit_variable):
        - (True, None) if forward checking succeeds
        - (False, culprit_var) if a domain becomes empty (culprit is the variable whose domain was wiped out)
    """
    for neighbor in csp.neighbors[var]:
        if len(domains[neighbor]) == 0:
            continue
        
        values_to_remove = []
        for neighbor_value in domains[neighbor]:
            temp_assignment = {var: value, neighbor: neighbor_value}
            
            consistent = True
            for constraint in csp.constraints[neighbor]:
                if var in constraint.variables and neighbor in constraint.variables:
                    if not constraint.is_satisfied(temp_assignment):
                        consistent = False
                        break
            
            if not consistent:
                values_to_remove.append(neighbor_value)
        
        for val in values_to_remove:
            domains[neighbor].discard(val)
        
        if len(domains[neighbor]) == 0:
            for constraint in csp.constraints[neighbor]:
                if var in constraint.variables and neighbor in constraint.variables:
                    constraint.increment_weight()
            return (False, neighbor)
    
    return (True, None)


def revise(csp: CSP, xi: Any, xj: Any, domains: Dict[Any, Set[Any]]) -> bool:
    """
    Make variable xi arc-consistent with xj.
    
    Removes values from xi's domain that have no consistent value in xj's domain.
    
    Args:
        csp: The constraint satisfaction problem
        xi: The variable to revise
        xj: The variable to check consistency with
        domains: Current domains (modified in-place)
        
    Returns:
        True if xi's domain was revised (values were removed), False otherwise
    """
    revised = False
    
    constraints_between = []
    for constraint in csp.constraints[xi]:
        if xj in constraint.variables and xi in constraint.variables:
            constraints_between.append(constraint)
    
    if not constraints_between:
        return False
    
    values_to_remove = []
    for xi_value in domains[xi]:
        satisfies = False
        for xj_value in domains[xj]:
            temp_assignment = {xi: xi_value, xj: xj_value}
            
            all_satisfied = True
            for constraint in constraints_between:
                if not constraint.is_satisfied(temp_assignment):
                    all_satisfied = False
                    break
            
            if all_satisfied:
                satisfies = True
                break
        
        if not satisfies:
            values_to_remove.append(xi_value)
            revised = True
    
    for val in values_to_remove:
        domains[xi].discard(val)
    
    return revised


def ac3(csp: CSP, domains: Dict[Any, Set[Any]], queue: Optional[List[Tuple[Any, Any]]] = None) -> Tuple[bool, Optional[Any]]:
    """
    Apply AC-3 (Arc Consistency 3) algorithm.
    
    Enforces arc consistency across all variable pairs. More thorough than
    forward checking but more computationally expensive.
    
    When a domain wipeout occurs, increments weights of constraints that caused it
    (for dom/wdeg heuristic).
    
    Args:
        csp: The constraint satisfaction problem
        domains: Current domains (modified in-place)
        queue: Optional initial queue of arcs to check. If None, uses all arcs.
        
    Returns:
        Tuple of (success, culprit_variable):
        - (True, None) if arc consistency is achieved
        - (False, culprit_var) if a domain becomes empty (culprit is the variable whose domain was wiped out)
    """
    if queue is None:
        queue = deque()
        for var in csp.variables:
            for neighbor in csp.neighbors[var]:
                queue.append((var, neighbor))
    else:
        queue = deque(queue)
    
    while queue:
        xi, xj = queue.popleft()
        
        if revise(csp, xi, xj, domains):
            if len(domains[xi]) == 0:
                for constraint in csp.constraints[xi]:
                    if xj in constraint.variables and xi in constraint.variables:
                        constraint.increment_weight()
                return (False, xi)
            
            for xk in csp.neighbors[xi]:
                if xk != xj:
                    queue.append((xk, xi))
    
    return (True, None)
