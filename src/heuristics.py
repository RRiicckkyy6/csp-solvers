"""
Heuristics for CSP solving.
Provides variable and value ordering strategies to improve search efficiency.
"""

from typing import Any, Dict, List, Set
from core import CSP


def select_unassigned_variable(assignment: Dict[Any, Any], csp: CSP, domains: Dict[Any, Set[Any]]) -> Any:
    """
    Select the next unassigned variable using MRV and Degree heuristics.
    
    Uses Minimum Remaining Values (MRV) heuristic: choose the variable with 
    the fewest legal values remaining. Ties are broken using the Degree heuristic:
    choose the variable involved in the most constraints with unassigned variables.
    
    Args:
        assignment: Current partial assignment
        csp: The constraint satisfaction problem
        domains: Current domains for all variables
        
    Returns:
        The next variable to assign
    """
    unassigned = [v for v in csp.variables if v not in assignment]
    
    if not unassigned:
        return None
    
    min_remaining = min(len(domains[var]) for var in unassigned)
    mrv_variables = [var for var in unassigned if len(domains[var]) == min_remaining]
    
    if len(mrv_variables) == 1:
        return mrv_variables[0]
    
    def count_unassigned_neighbors(var: Any) -> int:
        """Count how many unassigned neighbors this variable has."""
        return sum(1 for neighbor in csp.neighbors[var] if neighbor not in assignment)
    
    return max(mrv_variables, key=count_unassigned_neighbors)


def order_domain_values(var: Any, assignment: Dict[Any, Any], csp: CSP, domains: Dict[Any, Set[Any]]) -> List[Any]:
    """
    Order domain values using Least Constraining Value (LCV) heuristic.
    
    Prefers values that rule out the fewest choices for neighboring variables.
    This leaves maximum flexibility for future assignments.
    
    Args:
        var: The variable whose values to order
        assignment: Current partial assignment
        csp: The constraint satisfaction problem
        domains: Current domains for all variables
        
    Returns:
        List of values ordered by LCV heuristic (least constraining first)
    """
    if len(domains[var]) <= 1:
        return list(domains[var])
    
    def count_eliminated_values(value: Any) -> int:
        """
        Count how many values would be eliminated from neighbors' domains
        if we assign this value to var.
        """
        count = 0
        
        for neighbor in csp.neighbors[var]:
            if neighbor in assignment:
                continue
            
            for neighbor_value in domains[neighbor]:
                temp_assignment = assignment.copy()
                temp_assignment[var] = value
                temp_assignment[neighbor] = neighbor_value
                
                consistent = True
                for constraint in csp.constraints[neighbor]:
                    if all(v in temp_assignment for v in constraint.variables):
                        if not constraint.is_satisfied(temp_assignment):
                            consistent = False
                            break
                
                if not consistent:
                    count += 1
        
        return count
    
    values = list(domains[var])
    values.sort(key=count_eliminated_values)
    
    return values


def select_unassigned_variable_dom_wdeg(
    assignment: Dict[Any, Any], 
    csp: CSP, 
    domains: Dict[Any, Set[Any]]
) -> Any:
    """
    Select the next unassigned variable using dom/wdeg heuristic.
    
    The dom/wdeg (domain over weighted degree) heuristic is an adaptive strategy that:
    1. Maintains weights for each constraint (incremented when constraint causes failure)
    2. Computes weighted degree for each variable: sum of weights of constraints involving it
    3. Selects variable with minimum ratio: domain_size / weighted_degree
    
    This heuristic adapts to the problem structure by focusing on variables
    involved in frequently-failing constraints.
    
    Args:
        assignment: Current partial assignment
        csp: The constraint satisfaction problem
        domains: Current domains for all variables
        
    Returns:
        The next variable to assign
    """
    unassigned = [v for v in csp.variables if v not in assignment]
    
    if not unassigned:
        return None
    
    def weighted_degree(var: Any) -> float:
        """
        Calculate weighted degree: sum of weights of constraints involving var
        and at least one other unassigned variable.
        """
        total_weight = 0
        for constraint in csp.constraints[var]:
            unassigned_in_constraint = [v for v in constraint.variables 
                                       if v != var and v not in assignment]
            if unassigned_in_constraint:
                total_weight += constraint.weight
        
        return max(total_weight, 1)
    
    def dom_wdeg_ratio(var: Any) -> float:
        """Calculate dom/wdeg ratio for a variable."""
        domain_size = len(domains[var])
        wdeg = weighted_degree(var)
        return domain_size / wdeg
    
    return min(unassigned, key=dom_wdeg_ratio)


def increment_constraint_weights_on_failure(
    csp: CSP,
    var: Any,
    value: Any,
    assignment: Dict[Any, Any]
) -> None:
    """
    Increment weights of constraints that are violated by assigning value to var.
    
    This function should be called when a value assignment fails consistency check,
    to update constraint weights for the dom/wdeg heuristic.
    
    Args:
        csp: The constraint satisfaction problem
        var: The variable being assigned
        value: The value being assigned to var
        assignment: Current partial assignment
    """
    temp_assignment = assignment.copy()
    temp_assignment[var] = value
    
    for constraint in csp.constraints[var]:
        if all(v in temp_assignment for v in constraint.variables):
            if not constraint.is_satisfied(temp_assignment):
                constraint.increment_weight()
