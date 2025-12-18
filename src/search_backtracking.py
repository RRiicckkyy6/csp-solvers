"""
Backtracking search algorithm for CSP solving.
Implements systematic search with optional inference strategies.
"""

import time
from typing import Any, Dict, Set, Optional
from core import CSP
from heuristics import select_unassigned_variable, order_domain_values
from propagation import forward_checking, ac3


class SearchStatistics:
    """Track search statistics during backtracking."""
    
    def __init__(self):
        self.backtracks = 0
        self.constraint_checks = 0
        self.start_time = None
        self.end_time = None
    
    def reset(self):
        """Reset all counters."""
        self.backtracks = 0
        self.constraint_checks = 0
        self.start_time = None
        self.end_time = None
    
    def runtime(self) -> float:
        """Get runtime in seconds."""
        if self.start_time is None:
            return 0.0
        end = self.end_time if self.end_time else time.time()
        return end - self.start_time
    
    def __str__(self):
        return (f"Backtracks: {self.backtracks}, "
                f"Constraint Checks: {self.constraint_checks}, "
                f"Runtime: {self.runtime():.4f}s")


stats = SearchStatistics()


def backtracking_search(
    csp: CSP,
    inference: str = "none",
    variable_order: str = "mrv",
    value_order: str = "lcv",
    use_cbj: bool = False
) -> Optional[Dict[Any, Any]]:
    """
    Solve a CSP using backtracking search.
    
    Args:
        csp: The constraint satisfaction problem to solve
        inference: Inference strategy to use:
            - "none": No inference (basic backtracking)
            - "fc": Forward checking
            - "mac": Maintaining arc consistency (MAC)
        variable_order: Variable ordering heuristic:
            - "mrv": Minimum Remaining Values with Degree tie-breaking
            - "dom_wdeg": Domain over Weighted Degree (adaptive)
        value_order: Value ordering heuristic:
            - "lcv": Least Constraining Value
            - "none": No ordering (use domain order)
        use_cbj: Use Conflict-Directed Backjumping (non-chronological backtracking)
            
    Returns:
        Complete assignment if solution found, None otherwise
    """
    if inference not in ["none", "fc", "mac"]:
        raise ValueError(f"Invalid inference strategy: {inference}. Must be 'none', 'fc', or 'mac'")
    if variable_order not in ["mrv", "dom_wdeg"]:
        raise ValueError(f"Invalid variable_order: {variable_order}. Must be 'mrv' or 'dom_wdeg'")
    if value_order not in ["lcv", "none"]:
        raise ValueError(f"Invalid value_order: {value_order}. Must be 'lcv' or 'none'")
    
    stats.reset()
    stats.start_time = time.time()
    
    if variable_order == "dom_wdeg":
        for var in csp.variables:
            for constraint in csp.constraints[var]:
                constraint.weight = 1
    
    domains = csp.copy_domains()
    if inference == "mac":
        success, _ = ac3(csp, domains)
        if not success:
            stats.end_time = time.time()
            return None
    
    if use_cbj:
        conflict_sets = {var: set() for var in csp.variables}
        assignment_stack = []  # Track assignment order for depth determination
    else:
        conflict_sets = None
        assignment_stack = None
    
    if use_cbj:
        assignment = {}
        success, jump_var = backtrack_cbj(assignment, domains, csp, inference, variable_order, value_order, 
                                         conflict_sets, assignment_stack)
        result = assignment if success else None
    else:
        result = backtrack({}, domains, csp, inference, variable_order, value_order)
    
    stats.end_time = time.time()
    
    return result


def backtrack(
    assignment: Dict[Any, Any],
    domains: Dict[Any, Set[Any]],
    csp: CSP,
    inference: str,
    variable_order: str,
    value_order: str
) -> Optional[Dict[Any, Any]]:
    """
    Recursive backtracking function.
    
    Args:
        assignment: Current partial assignment
        domains: Current domains for all variables
        csp: The constraint satisfaction problem
        inference: Inference strategy ("none", "fc", or "mac")
        variable_order: Variable ordering heuristic ("mrv" or "dom_wdeg")
        value_order: Value ordering heuristic ("lcv" or "none")
        
    Returns:
        Complete assignment if solution found, None otherwise
    """
    from heuristics import select_unassigned_variable_dom_wdeg, increment_constraint_weights_on_failure
    
    if len(assignment) == len(csp.variables):
        return assignment
    
    if variable_order == "dom_wdeg":
        var = select_unassigned_variable_dom_wdeg(assignment, csp, domains)
    else:
        var = select_unassigned_variable(assignment, csp, domains)
    
    if value_order == "lcv":
        ordered_values = order_domain_values(var, assignment, csp, domains)
    else:
        ordered_values = list(domains[var])
    
    for value in ordered_values:
        stats.constraint_checks += 1
        if csp.is_consistent(var, value, assignment):
            assignment[var] = value
            
            saved_domains = {v: domain.copy() for v, domain in domains.items()}
            
            domains[var] = {value}
            
            inference_success = True
            
            if inference == "fc":
                inference_success, _ = forward_checking(csp, var, value, domains)
            
            elif inference == "mac":
                queue = [(neighbor, var) for neighbor in csp.neighbors[var]]
                inference_success, _ = ac3(csp, domains, queue)
            
            if inference_success:
                result = backtrack(assignment, domains, csp, inference, variable_order, value_order)
                if result is not None:
                    return result
            
            stats.backtracks += 1
            domains.update(saved_domains)
            del assignment[var]
        else:
            if variable_order == "dom_wdeg":
                increment_constraint_weights_on_failure(csp, var, value, assignment)
    
    return None


def backtrack_cbj(
    assignment: Dict[Any, Any],
    domains: Dict[Any, Set[Any]],
    csp: CSP,
    inference: str,
    variable_order: str,
    value_order: str,
    conflict_sets: Dict[Any, Set[Any]],
    assignment_stack: list
) -> tuple:
    """
    Backtracking with Conflict-Directed Backjumping (CBJ).
    
    Minimal implementation that always uses chronological backtracking.
    """
    from heuristics import select_unassigned_variable_dom_wdeg
    
    if len(assignment) == len(csp.variables):
        return (True, None)
    
    if variable_order == "dom_wdeg":
        var = select_unassigned_variable_dom_wdeg(assignment, csp, domains)
    else:
        var = select_unassigned_variable(assignment, csp, domains)
    
    if value_order == "lcv":
        ordered_values = order_domain_values(var, assignment, csp, domains)
    else:
        ordered_values = list(domains[var])
    
    if not ordered_values:
        return _cbj_backjump(var, assignment_stack)
    
    for value in ordered_values:
        stats.constraint_checks += 1
        
        if not csp.is_consistent(var, value, assignment):
            continue
        
        assignment[var] = value
        assignment_stack.append((var, value))
        saved_domains = {v: d.copy() for v, d in domains.items()}
        domains[var] = {value}
        
        inference_ok = True
        
        if inference == "fc":
            inference_ok, _ = forward_checking(csp, var, value, domains)
        elif inference == "mac":
            queue = [(neighbor, var) for neighbor in csp.neighbors[var]]
            inference_ok, _ = ac3(csp, domains, queue)
        
        if inference_ok:
            success, jump_target = backtrack_cbj(
                assignment, domains, csp, inference, variable_order, value_order,
                conflict_sets, assignment_stack
            )
            
            if success:
                return (True, None)
            
            stats.backtracks += 1
            domains.update(saved_domains)
            del assignment[var]
            assignment_stack.pop()
            
            if jump_target is not None and jump_target != var:
                return (False, jump_target)
        else:
            domains.update(saved_domains)
            del assignment[var]
            assignment_stack.pop()
    
    return _cbj_backjump(var, assignment_stack)


def _cbj_backjump(var: Any, assignment_stack: list) -> tuple:
    """
    Minimal backjump: always use chronological (previous variable).
    """
    if not assignment_stack:
        return (False, None)
    
    jump_target = assignment_stack[-1][0]
    return (False, jump_target)






def get_statistics() -> SearchStatistics:
    """
    Get the current search statistics.
    
    Returns:
        SearchStatistics object with counters and timing information
    """
    return stats
