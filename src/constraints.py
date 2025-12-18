"""
Constraint definitions for CSP problems.
Provides reusable constraint classes for various CSP problems.
"""

from typing import Any, Dict
from core import Constraint


class BinaryConstraint(Constraint):
    """
    Binary constraint between two variables.
    Base class for constraints involving exactly two variables.
    """
    
    def __init__(self, var1: Any, var2: Any):
        """
        Initialize a binary constraint between two variables.
        
        Args:
            var1: First variable
            var2: Second variable
        """
        super().__init__([var1, var2])
        self.var1 = var1
        self.var2 = var2
    
    def is_satisfied(self, assignment: Dict[Any, Any]) -> bool:
        """
        Check if the constraint is satisfied given an assignment.
        
        Args:
            assignment: Dictionary mapping variables to their assigned values
            
        Returns:
            True if constraint is satisfied, False otherwise
        """
        if self.var1 not in assignment or self.var2 not in assignment:
            return True
        
        val1 = assignment[self.var1]
        val2 = assignment[self.var2]
        
        return self.is_satisfied_values(val1, val2)
    
    def is_satisfied_values(self, val1: Any, val2: Any) -> bool:
        """
        Check if the constraint is satisfied for two specific values.
        Override this method in subclasses to define specific constraint logic.
        
        Args:
            val1: Value for first variable
            val2: Value for second variable
            
        Returns:
            True if constraint is satisfied, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_satisfied_values")


class NotEqualConstraint(BinaryConstraint):
    """
    Constraint that two variables must have different values.
    Used for graph/map coloring problems.
    """
    
    def is_satisfied_values(self, val1: Any, val2: Any) -> bool:
        """
        Check that the two values are not equal.
        
        Args:
            val1: Value for first variable
            val2: Value for second variable
            
        Returns:
            True if val1 != val2, False otherwise
        """
        return val1 != val2
