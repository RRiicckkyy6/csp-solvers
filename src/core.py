"""
CSP (Constraint Satisfaction Problem) core module.
Defines the CSP object model and constraint representation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set


class Constraint(ABC):
    """Abstract base class for constraints."""
    
    def __init__(self, variables: List[Any]):
        self.variables = variables
        self.weight = 1
    
    @abstractmethod
    def is_satisfied(self, assignment: Dict[Any, Any]) -> bool:
        """Check if the constraint is satisfied given an assignment."""
        pass
    
    def increment_weight(self) -> None:
        """Increment constraint weight when it causes a failure (for dom/wdeg)."""
        self.weight += 1


class CSP:
    """
    Constraint Satisfaction Problem representation.
    
    Attributes:
        variables: List of variables in the CSP
        domains: Dictionary mapping each variable to its set of possible values
        constraints: Dictionary mapping each variable to list of constraints involving it
        neighbors: Dictionary mapping each variable to set of neighboring variables
    """
    
    def __init__(self):
        self.variables: List[Any] = []
        self.domains: Dict[Any, Set[Any]] = {}
        self.constraints: Dict[Any, List[Constraint]] = {}
        self.neighbors: Dict[Any, Set[Any]] = {}
    
    def add_variable(self, var: Any, domain: Set[Any]) -> None:
        """
        Add a variable to the CSP with its domain.
        
        Args:
            var: The variable to add
            domain: Set of possible values for the variable
        """
        self.variables.append(var)
        self.domains[var] = set(domain)
        self.constraints[var] = []
        self.neighbors[var] = set()
    
    def add_constraint(self, constraint: Constraint) -> None:
        """
        Add a constraint to the CSP.
        
        Args:
            constraint: The constraint to add
        """
        for var in constraint.variables:
            if var not in self.variables:
                raise ValueError(f"Variable {var} not in CSP")
            self.constraints[var].append(constraint)
            
            for other_var in constraint.variables:
                if other_var != var:
                    self.neighbors[var].add(other_var)
    
    def is_consistent(self, var: Any, value: Any, assignment: Dict[Any, Any]) -> bool:
        """
        Check if assigning value to var is consistent with current assignment.
        
        Args:
            var: The variable to assign
            value: The value to assign to var
            assignment: Current partial assignment
            
        Returns:
            True if the assignment is consistent, False otherwise
        """
        temp_assignment = assignment.copy()
        temp_assignment[var] = value
        
        for constraint in self.constraints[var]:
            if all(v in temp_assignment for v in constraint.variables):
                if not constraint.is_satisfied(temp_assignment):
                    return False
        
        return True
    
    def copy_domains(self) -> Dict[Any, Set[Any]]:
        """
        Create a deep copy of the domains dictionary.
        Important for backtracking to restore domain states.
        
        Returns:
            A deep copy of the domains dictionary
        """
        return {var: domain.copy() for var, domain in self.domains.items()}
