"""
Unified solver interface for CSP problems.
Provides a single entry point for all solving methods.
"""

from typing import Any, Dict, Optional, Tuple, Union
from core import CSP
from search_backtracking import backtracking_search, get_statistics, SearchStatistics
from search_local import min_conflicts, get_local_statistics, LocalSearchStatistics


def solve(
    csp: CSP,
    inference: str = "none",
    variable_order: str = "mrv",
    value_order: str = "lcv",
    max_steps: int = 100000,
    use_cbj: bool = False
) -> Tuple[Optional[Dict[Any, Any]], Union[SearchStatistics, LocalSearchStatistics]]:
    """
    Solve a CSP using the specified configuration.
    
    Unified interface for CSP solving with explicit control over inference and heuristics.
    
    Args:
        csp: The constraint satisfaction problem to solve
        inference: Inference/propagation strategy:
            - "none": No inference (basic backtracking)
            - "fc": Forward checking
            - "mac": Maintaining arc consistency (MAC)
            - "min_conflicts": Local search with min-conflicts
        variable_order: Variable ordering heuristic (ignored for min_conflicts):
            - "mrv": Minimum Remaining Values with Degree tie-breaking
            - "dom_wdeg": Domain over Weighted Degree (adaptive)
        value_order: Value ordering heuristic (ignored for min_conflicts):
            - "lcv": Least Constraining Value
            - "none": No ordering (use domain order)
        max_steps: Maximum steps for min-conflicts local search
        use_cbj: Use Conflict-Directed Backjumping (non-chronological backtracking)
                 Orthogonal to inference and heuristics. Ignored for min_conflicts.
        
    Returns:
        Tuple of (solution, statistics):
            - solution: Dictionary mapping variables to values if solved, None otherwise
            - statistics: Statistics object with performance metrics
            
    Raises:
        ValueError: If inference, variable_order, or value_order is not recognized
    """
    valid_inference = ["none", "fc", "mac", "min_conflicts"]
    valid_var_order = ["mrv", "dom_wdeg"]
    valid_val_order = ["lcv", "none"]
    
    if inference not in valid_inference:
        raise ValueError(
            f"Invalid inference: {inference}. Must be one of {valid_inference}"
        )
    if variable_order not in valid_var_order:
        raise ValueError(
            f"Invalid variable_order: {variable_order}. Must be one of {valid_var_order}"
        )
    if value_order not in valid_val_order:
        raise ValueError(
            f"Invalid value_order: {value_order}. Must be one of {valid_val_order}"
        )
    
    if inference == "min_conflicts":
        solution = min_conflicts(csp, max_steps=max_steps)
        statistics = get_local_statistics()
    else:
        solution = backtracking_search(
            csp, 
            inference=inference,
            variable_order=variable_order,
            value_order=value_order,
            use_cbj=use_cbj
        )
        statistics = get_statistics()
    
    return solution, statistics


def print_solution(solution: Optional[Dict[Any, Any]], statistics: Union[SearchStatistics, LocalSearchStatistics]) -> None:
    """
    Print the solution and statistics in a readable format.
    
    Args:
        solution: The solution assignment (or None if no solution found)
        statistics: Statistics object from the search
    """
    print("=" * 60)
    if solution is not None:
        print("✓ Solution found!")
        print("\nAssignment:")
        for var, value in sorted(solution.items()):
            print(f"  {var}: {value}")
    else:
        print("✗ No solution found")
    
    print("\nStatistics:")
    print(f"  {statistics}")
    print("=" * 60)


def compare_inference_methods(
    csp: CSP,
    methods: list = None,
    variable_order: str = "mrv",
    value_order: str = "lcv"
) -> Dict[str, Tuple]:
    """
    Compare multiple inference methods on the same CSP instance.
    
    Args:
        csp: The constraint satisfaction problem to solve
        methods: List of inference methods to compare (default: all)
        variable_order: Variable ordering heuristic to use
        value_order: Value ordering heuristic to use
        
    Returns:
        Dictionary mapping method name to (solution, statistics) tuple
    """
    if methods is None:
        methods = ["none", "fc", "mac", "min_conflicts"]
    
    results = {}
    
    for method in methods:
        print(f"\nSolving with {method.upper()} (var={variable_order}, val={value_order})...")
        solution, stats = solve(
            csp, 
            inference=method,
            variable_order=variable_order,
            value_order=value_order
        )
        results[method] = (solution, stats)
        print_solution(solution, stats)
    
    return results
