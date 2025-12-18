"""
Sudoku Dataset Generator - Creates a collection of the hardest Sudoku puzzles.

Generates random Sudoku puzzles with 17-25 clues, solves them to measure difficulty,
and keeps only the top 5% hardest puzzles based on solving time.
"""

import json
import random
import time
from typing import List, Dict, Tuple
from problem_sudoku import generate_solved_sudoku, create_sudoku
from solver import solve


def generate_random_sudoku_puzzle(num_clues: int) -> Tuple[Dict[Tuple[int, int], int], str]:
    """
    Generate a random Sudoku puzzle with a specific number of clues.
    
    Args:
        num_clues: Number of given clues (17-25 for hard puzzles)
        
    Returns:
        Tuple of (initial_values dict, puzzle_string)
    """
    solved_grid = generate_solved_sudoku()
    
    all_positions = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(all_positions)
    
    initial_values = {}
    for pos in all_positions[:num_clues]:
        initial_values[pos] = solved_grid[pos]
    
    puzzle_string = ""
    for i in range(9):
        for j in range(9):
            if (i, j) in initial_values:
                puzzle_string += str(initial_values[(i, j)])
            else:
                puzzle_string += "0"
    
    return initial_values, puzzle_string


def measure_puzzle_difficulty(puzzle_string: str, inference: str = "none") -> Dict:
    """
    Measure the difficulty of a Sudoku puzzle by solving it.
    
    Args:
        puzzle_string: 81-character string representation of the puzzle
        inference: Inference method to use for solving
        
    Returns:
        Dictionary with difficulty metrics
    """
    initial_values = {}
    for idx, char in enumerate(puzzle_string):
        if char != '0':
            i = idx // 9
            j = idx % 9
            initial_values[(i, j)] = int(char)
    
    csp = create_sudoku(initial_values)
    
    start_time = time.time()
    solution, stats = solve(
        csp,
        inference=inference,
        variable_order="mrv",
        value_order="lcv",
        use_cbj=False
    )
    solve_time = time.time() - start_time
    
    return {
        'puzzle': puzzle_string,
        'num_clues': len(initial_values),
        'solvable': solution is not None,
        'solve_time': solve_time,
        'backtracks': stats.backtracks,
        'constraint_checks': stats.constraint_checks
    }


def generate_hardest_sudoku_dataset(
    num_puzzles: int = 1000,
    min_clues: int = 17,
    max_clues: int = 25,
    top_percent: float = 5.0,
    inference: str = "none",
    output_file: str = "hardest_sudoku.json",
    verbose: bool = True
):
    """
    Generate a dataset of the hardest Sudoku puzzles.
    
    Args:
        num_puzzles: Total number of puzzles to generate and test
        min_clues: Minimum number of clues
        max_clues: Maximum number of clues
        top_percent: Percentage of hardest puzzles to keep (default: 5%)
        inference: Inference method to use for measuring difficulty
        output_file: Output JSON filename
        verbose: Print progress messages
    """
    if verbose:
        print("="*80)
        print("Hardest Sudoku Dataset Generator")
        print("="*80)
        print(f"\nGenerating {num_puzzles} puzzles with {min_clues}-{max_clues} clues...")
        print(f"Measuring difficulty using '{inference}' inference...")
        print(f"Keeping top {top_percent}% hardest puzzles\n")
    
    puzzles_data = []
    successful_count = 0
    
    for i in range(num_puzzles):
        if verbose and (i + 1) % 50 == 0:
            print(f"Progress: {i+1}/{num_puzzles} puzzles generated...", end="\r")
        
        num_clues = random.randint(min_clues, max_clues)
        initial_values, puzzle_string = generate_random_sudoku_puzzle(num_clues)
        
        try:
            metrics = measure_puzzle_difficulty(puzzle_string, inference)
            
            if metrics['solvable']:
                puzzles_data.append(metrics)
                successful_count += 1
        except Exception as e:
            if verbose:
                print(f"\nError with puzzle {i+1}: {e}")
            continue
    
    if verbose:
        print(f"\nProgress: {num_puzzles}/{num_puzzles} puzzles generated.     ")
        print(f"\nSuccessfully generated and solved: {successful_count}/{num_puzzles} puzzles")
    
    puzzles_data.sort(key=lambda x: (x['solve_time'], x['backtracks']), reverse=True)
    
    num_to_keep = max(1, int(len(puzzles_data) * top_percent / 100))
    hardest_puzzles = puzzles_data[:num_to_keep]
    
    if verbose:
        print(f"\nKeeping top {num_to_keep} hardest puzzles ({top_percent}%)")
        print(f"\nDifficulty Statistics:")
        print(f"  Hardest puzzle:")
        print(f"    - Solve time: {hardest_puzzles[0]['solve_time']:.4f}s")
        print(f"    - Backtracks: {hardest_puzzles[0]['backtracks']}")
        print(f"    - Constraint checks: {hardest_puzzles[0]['constraint_checks']}")
        print(f"    - Clues: {hardest_puzzles[0]['num_clues']}")
        
        print(f"\n  Easiest in top {top_percent}%:")
        print(f"    - Solve time: {hardest_puzzles[-1]['solve_time']:.4f}s")
        print(f"    - Backtracks: {hardest_puzzles[-1]['backtracks']}")
        print(f"    - Constraint checks: {hardest_puzzles[-1]['constraint_checks']}")
        print(f"    - Clues: {hardest_puzzles[-1]['num_clues']}")
        
        avg_time = sum(p['solve_time'] for p in hardest_puzzles) / len(hardest_puzzles)
        avg_bt = sum(p['backtracks'] for p in hardest_puzzles) / len(hardest_puzzles)
        avg_clues = sum(p['num_clues'] for p in hardest_puzzles) / len(hardest_puzzles)
        
        print(f"\n  Average (top {top_percent}%):")
        print(f"    - Solve time: {avg_time:.4f}s")
        print(f"    - Backtracks: {avg_bt:.1f}")
        print(f"    - Clues: {avg_clues:.1f}")
    

    output_data = {
        'metadata': {
            'total_generated': num_puzzles,
            'total_solved': successful_count,
            'num_kept': len(hardest_puzzles),
            'top_percent': top_percent,
            'min_clues': min_clues,
            'max_clues': max_clues,
            'inference_method': inference,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        },
        'puzzles': hardest_puzzles
    }
    
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    if verbose:
        print(f"\n✓ Dataset saved to: {output_file}")
        print("="*80)
    
    return hardest_puzzles


def load_hardest_sudoku_dataset(filename: str = "hardest_sudoku.json") -> List[Dict]:
    """
    Load a previously generated dataset of hard Sudoku puzzles.
    
    Args:
        filename: JSON file to load
        
    Returns:
        List of puzzle dictionaries
    """
    with open(filename, 'r') as f:
        data = json.load(f)
    
    return data['puzzles']


def export_as_puzzle_strings(json_file: str = "hardest_sudoku.json", 
                             output_file: str = "hardest_sudoku_strings.txt"):
    """
    Export puzzles from JSON as simple string format (one per line).
    
    Args:
        json_file: Input JSON file
        output_file: Output text file
    """
    puzzles = load_hardest_sudoku_dataset(json_file)
    
    with open(output_file, 'w') as f:
        for puzzle_data in puzzles:
            f.write(puzzle_data['puzzle'] + '\n')
    
    print(f"✓ Exported {len(puzzles)} puzzles to: {output_file}")


def main():
    """Main function to generate hardest Sudoku dataset."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate hardest Sudoku puzzle dataset')
    parser.add_argument('-n', '--num-puzzles', type=int, default=1000,
                       help='Number of puzzles to generate (default: 1000)')
    parser.add_argument('--min-clues', type=int, default=17,
                       help='Minimum number of clues (default: 17)')
    parser.add_argument('--max-clues', type=int, default=25,
                       help='Maximum number of clues (default: 25)')
    parser.add_argument('-p', '--top-percent', type=float, default=1,
                       help='Percentage of hardest puzzles to keep (default: 1)')
    parser.add_argument('-i', '--inference', type=str, default='fc',
                       choices=['none', 'fc', 'mac'],
                       help='Inference method for measuring difficulty (default: fc)')
    parser.add_argument('-o', '--output', type=str, default='hardest_sudoku.json',
                       help='Output JSON file (default: hardest_sudoku.json)')
    parser.add_argument('--export-strings', action='store_true',
                       help='Also export as text file with one puzzle per line')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Suppress progress messages')
    
    args = parser.parse_args()
    
    hardest_puzzles = generate_hardest_sudoku_dataset(
        num_puzzles=args.num_puzzles,
        min_clues=args.min_clues,
        max_clues=args.max_clues,
        top_percent=args.top_percent,
        inference=args.inference,
        output_file=args.output,
        verbose= not args.quiet
    )
    
    if args.export_strings:
        txt_file = args.output.replace('.json', '_strings.txt')
        export_as_puzzle_strings(args.output, txt_file)


if __name__ == "__main__":
    main()
