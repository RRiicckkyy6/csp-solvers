"""
Test script to verify Sudoku generation creates valid grids.
"""

from problem_sudoku import generate_solved_sudoku, create_sudoku, print_sudoku, generate_sudoku
from solver import solve


def verify_sudoku_grid(grid):
    """
    Verify that a completed Sudoku grid is valid.
    
    Returns True if valid, False otherwise.
    """
    for i in range(9):
        row_values = [grid[(i, j)] for j in range(9)]
        if sorted(row_values) != list(range(1, 10)):
            print(f"Invalid row {i}: {row_values}")
            return False
    
    for j in range(9):
        col_values = [grid[(i, j)] for i in range(9)]
        if sorted(col_values) != list(range(1, 10)):
            print(f"Invalid column {j}: {col_values}")
            return False
    
    for box_row in range(3):
        for box_col in range(3):
            box_values = []
            for i in range(box_row * 3, box_row * 3 + 3):
                for j in range(box_col * 3, box_col * 3 + 3):
                    box_values.append(grid[(i, j)])
            if sorted(box_values) != list(range(1, 10)):
                print(f"Invalid box ({box_row}, {box_col}): {box_values}")
                return False
    
    return True


def test_generation():
    """Test that generated Sudoku grids are valid."""
    print("Testing Sudoku generation...")
    print("=" * 50)
    
    print("\n1. Testing complete grid generation (10 samples)...")
    for i in range(10):
        grid = generate_solved_sudoku()
        if verify_sudoku_grid(grid):
            print(f"  Sample {i+1}: ✓ Valid")
        else:
            print(f"  Sample {i+1}: ✗ INVALID!")
            print_sudoku(grid)
            return False
    
    print("\n2. Testing puzzle generation with solving...")
    difficulties = ["easy", "medium", "hard", "expert"]
    
    for difficulty in difficulties:
        print(f"\n  Testing {difficulty} puzzles (3 samples)...")
        for i in range(3):
            csp = generate_sudoku(difficulty)
            
            initial_values = {var: list(domain)[0] 
                            for var, domain in csp.domains.items() 
                            if len(domain) == 1}
            num_clues = len(initial_values)
            
            solution, stats = solve(csp, inference="mac", variable_order="mrv", value_order="lcv")
            
            if solution:
                if verify_sudoku_grid(solution):
                    print(f"    Sample {i+1}: ✓ Valid puzzle with {num_clues} clues, solved in {stats.runtime():.3f}s")
                else:
                    print(f"    Sample {i+1}: ✗ Solution is INVALID!")
                    print("Initial:")
                    print_sudoku(initial_values)
                    print("Solution:")
                    print_sudoku(solution)
                    return False
            else:
                print(f"    Sample {i+1}: ✗ NO SOLUTION FOUND! ({num_clues} clues)")
                print("Puzzle:")
                print_sudoku(initial_values)
                return False
    
    print("\n" + "=" * 50)
    print("All tests passed! ✓")
    return True


if __name__ == "__main__":
    test_generation()
