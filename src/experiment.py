"""
Experiment runner for CSP solver benchmarking.
Generates instances, runs solvers, and aggregates performance metrics.
"""

import csv
import statistics
from typing import List, Dict, Any
from problem_graph_coloring import random_graph_coloring
from problem_sudoku import generate_sudoku
from solver import solve


class ExperimentResult:
    """Store results from a single experiment trial."""
    
    def __init__(self, n: int, p: float, k: int, config_name: str, 
                 inference: str = None, var_order: str = None, val_order: str = None, use_cbj: bool = False):
        self.n = n
        self.p = p
        self.k = k
        self.config_name = config_name  # For display
        self.inference = inference
        self.var_order = var_order
        self.val_order = val_order
        self.use_cbj = use_cbj
        self.solved = []
        self.runtimes = []
        self.backtracks = []
        self.constraint_checks = []
        self.steps = []
    
    def add_trial(self, solution: Any, stats: Any):
        """Add results from a single trial."""
        self.solved.append(solution is not None)
        self.runtimes.append(stats.runtime())
        
        if hasattr(stats, 'backtracks'):
            self.backtracks.append(stats.backtracks)
            self.constraint_checks.append(stats.constraint_checks)
        elif hasattr(stats, 'steps'):
            self.steps.append(stats.steps)
            self.constraint_checks.append(stats.conflict_checks)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all trials."""
        success_rate = sum(self.solved) / len(self.solved) if self.solved else 0
        
        summary = {
            'problem_type': 'graph_coloring',
            'n': self.n,
            'p': self.p,
            'k': self.k,
            'config': self.config_name,
            'inference': self.inference,
            'var_order': self.var_order,
            'val_order': self.val_order,
            'use_cbj': self.use_cbj,
            'trials': len(self.solved),
            'success_rate': success_rate,
            'avg_runtime': statistics.mean(self.runtimes) if self.runtimes else 0,
            'std_runtime': statistics.stdev(self.runtimes) if len(self.runtimes) > 1 else 0,
            'avg_checks': statistics.mean(self.constraint_checks) if self.constraint_checks else 0,
        }
        
        if self.backtracks:
            summary['avg_backtracks'] = statistics.mean(self.backtracks)
        
        if self.steps:
            summary['avg_steps'] = statistics.mean(self.steps)
        
        return summary


class SudokuExperimentResult:
    """Store results from Sudoku experiment trials."""
    
    def __init__(self, difficulty: str, config_name: str, 
                 inference: str = None, var_order: str = None, val_order: str = None, use_cbj: bool = False):
        self.difficulty = difficulty
        self.config_name = config_name
        self.inference = inference
        self.var_order = var_order
        self.val_order = val_order
        self.use_cbj = use_cbj
        self.solved = []
        self.runtimes = []
        self.backtracks = []
        self.constraint_checks = []
        self.steps = []
    
    def add_trial(self, solution: Any, stats: Any):
        """Add results from a single trial."""
        self.solved.append(solution is not None)
        self.runtimes.append(stats.runtime())
        
        if hasattr(stats, 'backtracks'):
            self.backtracks.append(stats.backtracks)
            self.constraint_checks.append(stats.constraint_checks)
        elif hasattr(stats, 'steps'):
            self.steps.append(stats.steps)
            self.constraint_checks.append(stats.conflict_checks)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for all trials."""
        success_rate = sum(self.solved) / len(self.solved) if self.solved else 0
        
        summary = {
            'problem_type': 'sudoku',
            'difficulty': self.difficulty,
            'config': self.config_name,
            'inference': self.inference,
            'var_order': self.var_order,
            'val_order': self.val_order,
            'use_cbj': self.use_cbj,
            'trials': len(self.solved),
            'success_rate': success_rate,
            'avg_runtime': statistics.mean(self.runtimes) if self.runtimes else 0,
            'std_runtime': statistics.stdev(self.runtimes) if len(self.runtimes) > 1 else 0,
            'avg_checks': statistics.mean(self.constraint_checks) if self.constraint_checks else 0,
        }
        
        if self.backtracks:
            summary['avg_backtracks'] = statistics.mean(self.backtracks)
        
        if self.steps:
            summary['avg_steps'] = statistics.mean(self.steps)
        
        return summary


def run_trials(
    n: int,
    p: float,
    k: int,
    inference_methods: List[str] = None,
    variable_orders: List[str] = None,
    value_order: str = "lcv",
    trials: int = 10,
    test_cbj: bool = False,
    verbose: bool = True
) -> Dict[str, ExperimentResult]:
    """
    Run multiple trials for a given problem configuration.
    Tests all combinations of inference methods and variable orderings.
    
    Args:
        n: Number of vertices
        p: Edge probability
        k: Number of colors
        inference_methods: List of inference methods to test (default: all)
        variable_orders: List of variable ordering heuristics (default: all)
        value_order: Value ordering heuristic ("lcv" or "none")
        trials: Number of trials to run
        test_cbj: If True, test both with and without CBJ for each configuration
        verbose: Print progress messages
        
    Returns:
        Dictionary mapping configuration name to ExperimentResult
    """
    if inference_methods is None:
        inference_methods = ["none", "fc", "mac", "min_conflicts"]
    if variable_orders is None:
        variable_orders = ["mrv", "dom_wdeg"]
    
    combinations = []
    for inference in inference_methods:
        if inference == "min_conflicts":
            combinations.append((inference, None, value_order, False))
        else:
            for var_order in variable_orders:
                combinations.append((inference, var_order, value_order, False))
                if test_cbj:
                    combinations.append((inference, var_order, value_order, True))
    
    if verbose:
        print(f"\nRunning experiments: n={n}, p={p:.2f}, k={k}, trials={trials}")
        print(f"  Testing {len(combinations)} configurations" + (" (including CBJ variants)" if test_cbj else ""))
    
    results = {}
    for inference, var_order, val_order, use_cbj in combinations:
        if inference == "min_conflicts":
            config_name = f"{inference}"
        else:
            cbj_suffix = "+CBJ" if use_cbj else ""
            config_name = f"{inference}+{var_order}+{val_order}{cbj_suffix}"
        results[config_name] = ExperimentResult(
            n, p, k, config_name, inference, var_order, val_order, use_cbj
        )
    
    for trial in range(trials):
        if verbose:
            print(f"  Trial {trial + 1}/{trials}...", end=" ")
        
        csp = random_graph_coloring(n, p, k)
        
        for config_name, result in results.items():
            solution, stats = solve(
                csp, 
                inference=result.inference,
                variable_order=result.var_order if result.var_order else "mrv",
                value_order=result.val_order,
                use_cbj=result.use_cbj
            )
            result.add_trial(solution, stats)
        
        if verbose:
            print("✓")
    
    return results


def run_sudoku_trials(
    difficulty: str,
    inference_methods: List[str] = None,
    variable_orders: List[str] = None,
    value_order: str = "lcv",
    trials: int = 10,
    test_cbj: bool = False,
    verbose: bool = True
) -> Dict[str, SudokuExperimentResult]:
    """
    Run multiple trials for a given Sudoku difficulty.
    Tests all combinations of inference methods and variable orderings.
    
    Args:
        difficulty: Sudoku difficulty level ("easy", "medium", "hard", "expert")
        inference_methods: List of inference methods to test (default: all)
        variable_orders: List of variable ordering heuristics (default: all)
        value_order: Value ordering heuristic ("lcv" or "none")
        trials: Number of trials to run
        test_cbj: If True, test both with and without CBJ for each configuration
        verbose: Print progress messages
        
    Returns:
        Dictionary mapping configuration name to SudokuExperimentResult
    """
    if inference_methods is None:
        inference_methods = ["none", "fc", "mac", "min_conflicts"]
    if variable_orders is None:
        variable_orders = ["mrv", "dom_wdeg"]
    
    combinations = []
    for inference in inference_methods:
        if inference == "min_conflicts":
            combinations.append((inference, None, value_order, False))
        else:
            for var_order in variable_orders:
                combinations.append((inference, var_order, value_order, False))
                if test_cbj:
                    combinations.append((inference, var_order, value_order, True))
    
    if verbose:
        print(f"\nRunning Sudoku experiments: difficulty={difficulty}, trials={trials}")
        print(f"  Testing {len(combinations)} configurations" + (" (including CBJ variants)" if test_cbj else ""))
    
    results = {}
    for inference, var_order, val_order, use_cbj in combinations:
        if inference == "min_conflicts":
            config_name = f"{inference}"
        else:
            cbj_suffix = "+CBJ" if use_cbj else ""
            config_name = f"{inference}+{var_order}+{val_order}{cbj_suffix}"
        results[config_name] = SudokuExperimentResult(
            difficulty, config_name, inference, var_order, val_order, use_cbj
        )
    
    for trial in range(trials):
        if verbose:
            print(f"  Trial {trial + 1}/{trials}...", end=" ")
        
        csp = generate_sudoku(difficulty)
        
        for config_name, result in results.items():
            solution, stats = solve(
                csp, 
                inference=result.inference,
                variable_order=result.var_order if result.var_order else "mrv",
                value_order=result.val_order,
                use_cbj=result.use_cbj
            )
            result.add_trial(solution, stats)
        
        if verbose:
            print("✓")
    
    return results


def run_experiment_suite(
    configurations: List[Dict[str, Any]],
    inference_methods: List[str] = None,
    variable_orders: List[str] = None,
    value_order: str = "lcv",
    trials: int = 10,
    test_cbj: bool = False,
    output_csv: str = None
) -> List[Dict[str, Any]]:
    """
    Run a suite of experiments with different configurations.
    Tests all combinations of inference methods and variable orderings.
    
    Args:
        configurations: List of dicts with 'n', 'p', 'k' keys
        inference_methods: List of inference methods to test
        variable_orders: List of variable ordering heuristics
        value_order: Value ordering heuristic
        trials: Number of trials per configuration
        test_cbj: If True, test both with and without CBJ for each configuration
        output_csv: Optional filename to save results
        
    Returns:
        List of summary dictionaries
    """
    if inference_methods is None:
        inference_methods = ["none", "fc", "mac", "min_conflicts"]
    if variable_orders is None:
        variable_orders = ["mrv", "dom_wdeg"]
    
    all_summaries = []
    
    for config in configurations:
        n = config['n']
        p = config['p']
        k = config['k']
        
        results = run_trials(
            n, p, k,
            inference_methods=inference_methods,
            variable_orders=variable_orders,
            value_order=value_order,
            trials=trials,
            test_cbj=test_cbj
        )
        
        for config_name, result in results.items():
            summary = result.get_summary()
            all_summaries.append(summary)
    
    print_results_table(all_summaries)
    
    if output_csv:
        save_results_csv(all_summaries, output_csv)
        print(f"\n✓ Results saved to {output_csv}")
    
    return all_summaries


def run_sudoku_experiment_suite(
    difficulties: List[str],
    inference_methods: List[str] = None,
    variable_orders: List[str] = None,
    value_order: str = "lcv",
    trials: int = 10,
    test_cbj: bool = False,
    output_csv: str = None
) -> List[Dict[str, Any]]:
    """
    Run a suite of Sudoku experiments with different difficulties.
    Tests all combinations of inference methods and variable orderings.
    
    Args:
        difficulties: List of difficulty levels ("easy", "medium", "hard", "expert")
        inference_methods: List of inference methods to test
        variable_orders: List of variable ordering heuristics
        value_order: Value ordering heuristic
        trials: Number of trials per difficulty level
        test_cbj: If True, test both with and without CBJ for each configuration
        output_csv: Optional filename to save results
        
    Returns:
        List of summary dictionaries
    """
    if inference_methods is None:
        inference_methods = ["none", "fc", "mac", "min_conflicts"]
    if variable_orders is None:
        variable_orders = ["mrv", "dom_wdeg"]
    
    all_summaries = []
    
    for difficulty in difficulties:
        results = run_sudoku_trials(
            difficulty,
            inference_methods=inference_methods,
            variable_orders=variable_orders,
            value_order=value_order,
            trials=trials,
            test_cbj=test_cbj
        )
        
        for config_name, result in results.items():
            summary = result.get_summary()
            all_summaries.append(summary)
    
    print_results_table(all_summaries)
    
    if output_csv:
        save_results_csv(all_summaries, output_csv)
        print(f"\n✓ Results saved to {output_csv}")
    
    return all_summaries


def print_results_table(summaries: List[Dict[str, Any]]):
    """Print results in a formatted table."""
    print("\n" + "=" * 120)
    print("EXPERIMENT RESULTS")
    print("=" * 120)
    
    header = f"{'Problem':<18} {'Configuration':<25} {'Success':<10} {'Avg Time':<12} {'Avg Checks':<15} {'Extra':<15}"
    print(header)
    print("-" * 120)
    
    for summary in summaries:
        if summary.get('problem_type') == 'sudoku':
            problem = f"Sudoku-{summary.get('difficulty', 'unknown')}"
        else:
            problem = f"n={summary.get('n', 0)},p={summary.get('p', 0):.1f},k={summary.get('k', 0)}"
        config = summary.get('config', summary.get('method', 'unknown'))
        success = f"{summary['success_rate']:.1%}"
        avg_time = f"{summary['avg_runtime']:.4f}s"
        avg_checks = f"{summary['avg_checks']:.0f}"
        
        if 'avg_backtracks' in summary:
            extra = f"BT: {summary['avg_backtracks']:.0f}"
        elif 'avg_steps' in summary:
            extra = f"Steps: {summary['avg_steps']:.0f}"
        else:
            extra = ""
        
        row = f"{problem:<18} {config:<25} {success:<10} {avg_time:<12} {avg_checks:<15} {extra:<15}"
        print(row)
    
    print("=" * 120)


def save_results_csv(summaries: List[Dict[str, Any]], filename: str):
    """Save results to a CSV file."""
    if not summaries:
        return
    
    fieldnames = ['problem_type', 'n', 'p', 'k', 'difficulty', 'config', 'inference', 'var_order', 'val_order', 'use_cbj',
                  'trials', 'success_rate', 'avg_runtime', 'std_runtime', 'avg_checks', 
                  'avg_backtracks', 'avg_steps']
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for summary in summaries:
            writer.writerow(summary)


def quick_experiment():
    """Run a quick experiment with common configurations.
    Tests all combinations of inference methods and variable orderings."""
    print("Running quick experiment suite...")
    print("Testing all combinations of inference methods and variable orderings")
    
    configurations = []
    
    for p in [0.1, 0.2, 0.3, 0.4, 0.5]:
        for k in [3, 4]:
            configurations.append({'n': 30, 'p': p, 'k': k})
    
    results = run_experiment_suite(
        configurations,
        inference_methods=["none", "fc", "mac", "min_conflicts"],
        variable_orders=["mrv", "dom_wdeg"],
        value_order="lcv",
        trials=5,
        output_csv="results.csv",
    )
    
    return results


def comprehensive_experiment():
    """Run a comprehensive experiment suite for paper results.
    Tests all combinations of inference methods and variable orderings."""
    print("Running comprehensive experiment suite...")
    print("Testing all combinations of inference methods and variable orderings")
    
    configurations = []
    
    for p in [0.16]:
        for k in [4]:
            configurations.append({'n': 50, 'p': p, 'k': k})
    
    results = run_experiment_suite(
        configurations,
        inference_methods=["min_conflicts"],
        variable_orders=["mrv", "dom_wdeg"],
        value_order="lcv",
        trials=5,
        output_csv="comprehensive_results.csv",
        test_cbj=True
    )
    
    return results


def sudoku_quick_experiment():
    """Run a quick experiment with Sudoku puzzles.
    Tests all combinations of inference methods and variable orderings."""
    print("Running quick Sudoku experiment suite...")
    print("Testing all combinations of inference methods and variable orderings")
    
    difficulties = ["easy", "medium", "hard"]
    
    results = run_sudoku_experiment_suite(
        difficulties,
        inference_methods=["none", "fc", "mac"],
        variable_orders=["mrv", "dom_wdeg"],
        value_order="lcv",
        trials=5,
        output_csv="sudoku_results.csv",
    )
    
    return results


def sudoku_comprehensive_experiment():
    """Run a comprehensive Sudoku experiment suite.
    Tests all combinations of inference methods and variable orderings."""
    print("Running comprehensive Sudoku experiment suite...")
    print("Testing all combinations of inference methods and variable orderings")
    
    difficulties = ["expert"]
    
    results = run_sudoku_experiment_suite(
        difficulties,
        inference_methods=["min_conflicts"],
        variable_orders=["mrv", "dom_wdeg"],
        value_order="lcv",
        trials=5,
        output_csv="sudoku_comprehensive_results.csv",
        test_cbj=True
    )
    
    return results


if __name__ == "__main__":
    comprehensive_experiment()
