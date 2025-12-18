# CSP Solver: A Generic Constraint Satisfaction Problem Framework

A modular, extensible Python framework for solving Constraint Satisfaction Problems (CSPs) with support for multiple inference strategies, variable/value ordering heuristics, and search algorithms.

## Features

### Search Algorithms
- **Backtracking Search**: Classic depth-first search with configurable inference and heuristics
- **Conflict-Directed Backjumping (CBJ)**: Non-chronological backtracking that skips irrelevant variables
- **Min-Conflicts Local Search**: Iterative repair algorithm for large-scale problems

### Inference Strategies
- **None**: Basic backtracking without domain reduction
- **Forward Checking (FC)**: Prunes domains of unassigned neighbors after each assignment
- **Maintaining Arc Consistency (MAC)**: Full arc consistency (AC-3) after each assignment

### Variable Ordering Heuristics
- **MRV (Minimum Remaining Values)**: Select variable with smallest domain, with degree tie-breaking
- **dom/wdeg (Domain over Weighted Degree)**: Adaptive heuristic that learns from failures

### Value Ordering Heuristics
- **LCV (Least Constraining Value)**: Choose value that rules out fewest choices for neighbors
- **None**: Use default domain order

## Project Structure

```
├── core.py                    # Core CSP and Constraint classes
├── constraints.py             # Constraint implementations (AllDifferent, etc.)
├── solver.py                  # Unified solver interface
├── search_backtracking.py     # Backtracking search with CBJ
├── search_local.py            # Min-conflicts local search
├── propagation.py             # AC-3 and forward checking
├── heuristics.py              # Variable and value ordering heuristics
├── problem_graph_coloring.py  # Graph coloring problem generator
├── problem_sudoku.py          # Sudoku problem (as binary CSP)
├── experiment.py              # Benchmarking framework
└── hardest_sudoku.json        # Collection of expert Sudoku puzzles
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/csp-solver.git
cd csp-solver

# No external dependencies required - uses Python standard library only
python --version  # Requires Python 3.7+
```

## Usage

### Basic Usage

```python
from solver import solve
from problem_graph_coloring import create_random_graph_coloring_csp
from problem_sudoku import create_sudoku_csp

# Solve a random graph coloring problem
csp = create_random_graph_coloring_csp(n=50, p=0.2, k=4)
solution, stats = solve(csp, inference="mac", variable_order="mrv", value_order="lcv")

if solution:
    print(f"Solution found in {stats.runtime():.3f}s")
    print(f"Backtracks: {stats.backtracks}")
else:
    print("No solution exists")
```

### Solving Sudoku

```python
from problem_sudoku import create_sudoku_csp, parse_sudoku_string

# From a string (81 characters, 0 = empty)
puzzle = "530070000600195000098000060800060003400803001700020006060000280000419005000080079"
csp = create_sudoku_csp(parse_sudoku_string(puzzle))
solution, stats = solve(csp, inference="mac", variable_order="mrv")

# Print the solved grid
if solution:
    for row in range(9):
        print([solution[(row, col)] for col in range(9)])
```

### Configuring the Solver

```python
from solver import solve

# Basic backtracking (no inference)
solution, stats = solve(csp, inference="none")

# Forward checking with MRV
solution, stats = solve(csp, inference="fc", variable_order="mrv")

# MAC with adaptive dom/wdeg heuristic
solution, stats = solve(csp, inference="mac", variable_order="dom_wdeg")

# With Conflict-Directed Backjumping
solution, stats = solve(csp, inference="fc", variable_order="mrv", use_cbj=True)

# Min-conflicts local search
solution, stats = solve(csp, inference="min_conflicts", max_steps=100000)
```

## Running Experiments

The framework includes a comprehensive benchmarking system:

```python
from experiment import run_graph_coloring_experiment, run_sudoku_experiment

# Run graph coloring experiments
run_graph_coloring_experiment(
    n_values=[30, 50],           # Number of vertices
    p_values=[0.1, 0.2],         # Edge probability
    k_values=[3, 4],             # Number of colors
    trials=10,                   # Trials per configuration
    test_cbj=True                # Include CBJ variants
)

# Run Sudoku experiments
run_sudoku_experiment(
    difficulties=["easy", "medium", "hard", "expert"],
    trials=10,
    test_cbj=True
)
```

### Sample Output

```
========================================================================================================
Problem            Configuration             Success    Avg Time     Avg Checks      Extra
--------------------------------------------------------------------------------------------------------
n=50,p=0.2,k=4     fc+mrv+lcv                60.0%      0.234s       3003            BT: 2993
n=50,p=0.2,k=4     mac+mrv+lcv               60.0%      0.295s       898             BT: 888
n=50,p=0.2,k=4     mac+dom_wdeg+lcv          60.0%      0.262s       589             BT: 579
========================================================================================================
```

## Algorithm Details

### Arc Consistency (AC-3)
Iteratively removes inconsistent values from domains until no more can be removed. A value is inconsistent if no value in the neighboring domain satisfies the constraint.

### Forward Checking
After assigning a variable, removes inconsistent values from the domains of unassigned neighbors. Detects failures earlier than basic backtracking.

### MRV Heuristic
Selects the variable with the fewest remaining values in its domain. Ties are broken by degree (most constraints with unassigned variables).

### dom/wdeg Heuristic
Adaptive heuristic that maintains constraint weights. When a constraint causes a domain wipeout, its weight is incremented. Variables are selected by domain size divided by weighted degree.

### Conflict-Directed Backjumping
Maintains conflict sets to track which variables caused value eliminations. When backtracking, jumps directly to the most recent conflicting variable instead of chronological backtracking.

## Extending the Framework

### Adding a New Problem Type

```python
from core import CSP, Constraint

class MyConstraint(Constraint):
    def __init__(self, variables):
        super().__init__(variables)
    
    def is_satisfied(self, assignment):
        # Return True if constraint is satisfied
        return True

def create_my_csp():
    variables = [...]
    domains = {var: set([...]) for var in variables}
    csp = CSP(variables, domains)
    
    # Add constraints
    csp.add_constraint(MyConstraint([var1, var2]))
    
    return csp
```

## Performance Tips

1. **Use MAC for hard problems**: More upfront pruning leads to smaller search trees
2. **Use dom/wdeg for repeated solving**: The adaptive heuristic improves over time
3. **Use min-conflicts for satisfiable instances**: Fast for problems known to have solutions
4. **CBJ helps most with weak inference**: With strong inference (MAC), most failures are caught early

## License

MIT License - feel free to use and modify for your projects.

## References

- Russell, S., & Norvig, P. (2020). *Artificial Intelligence: A Modern Approach* (4th ed.)
- Prosser, P. (1993). Hybrid algorithms for the constraint satisfaction problem. *Computational Intelligence*
- Boussemart, F., Hemery, F., Lecoutre, C., & Sais, L. (2004). Boosting systematic search by weighting constraints. *ECAI 2004*
