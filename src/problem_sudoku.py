"""
Sudoku problem generator.
Generates Sudoku CSP instances framed as binary constraint problems.
"""

import json
import os
import random
from typing import List, Tuple, Dict, Any, Set, Iterator
from core import CSP
from constraints import NotEqualConstraint

_expert_puzzle_iterator = None


def _get_expert_puzzle_iterator() -> Iterator[str]:
    """
    Get or create an iterator that yields expert puzzles from hardest_sudoku.json.
    The iterator cycles through puzzles indefinitely.
    
    Returns:
        Iterator that yields puzzle strings
    """
    global _expert_puzzle_iterator
    
    if _expert_puzzle_iterator is None:
        _expert_puzzle_iterator = _create_expert_puzzle_iterator()
    
    return _expert_puzzle_iterator


def _create_expert_puzzle_iterator() -> Iterator[str]:
    """
    Create an iterator that loads expert puzzles from hardest_sudoku.json.
    Cycles through the puzzles indefinitely.
    
    Yields:
        Puzzle strings from the dataset
    """
    dataset_file = "hardest_sudoku.json"
    
    if not os.path.exists(dataset_file):
        while True:
            for puzzle in EXPERT_PUZZLES:
                yield puzzle
    else:
        try:
            with open(dataset_file, 'r') as f:
                data = json.load(f)
            
            puzzles = []
            for puzzle_data in data:
                if 'puzzle_string' in puzzle_data:
                    puzzles.append(puzzle_data['puzzle_string'])
            
            if not puzzles:
                while True:
                    for puzzle in EXPERT_PUZZLES:
                        yield puzzle
            else:
                while True:
                    for puzzle in puzzles:
                        yield puzzle
        except Exception as e:
            print(f"Warning: Could not load {dataset_file}: {e}")
            print("Falling back to predefined EXPERT_PUZZLES")
            while True:
                for puzzle in EXPERT_PUZZLES:
                    yield puzzle

def create_sudoku(initial_values: Dict[Tuple[int, int], int] = None) -> CSP:
    """
    Create a Sudoku CSP instance.
    
    Sudoku is framed as a binary CSP where:
    - Variables: Each cell (i, j) where i is row (0-8) and j is column (0-8)
    - Domain: {1, 2, 3, 4, 5, 6, 7, 8, 9} for empty cells
    - Binary Constraints: NotEqual between all pairs of cells that:
      * Share the same row, OR
      * Share the same column, OR
      * Share the same 3x3 box
    
    Args:
        initial_values: Dictionary mapping (row, col) -> value for pre-filled cells
        
    Returns:
        CSP instance representing the Sudoku problem
    """
    csp = CSP()
    
    full_domain = set(range(1, 10))
    
    for i in range(9):
        for j in range(9):
            cell = (i, j)
            
            if initial_values and cell in initial_values:
                csp.add_variable(cell, {initial_values[cell]})
            else:
                csp.add_variable(cell, full_domain.copy())
    
    for i in range(9):
        for j1 in range(9):
            for j2 in range(j1 + 1, 9):
                constraint = NotEqualConstraint((i, j1), (i, j2))
                csp.add_constraint(constraint)
    
    for j in range(9):
        for i1 in range(9):
            for i2 in range(i1 + 1, 9):
                constraint = NotEqualConstraint((i1, j), (i2, j))
                csp.add_constraint(constraint)
    
    for box_row in range(3):
        for box_col in range(3):
            cells_in_box = []
            for i in range(box_row * 3, box_row * 3 + 3):
                for j in range(box_col * 3, box_col * 3 + 3):
                    cells_in_box.append((i, j))
            
            for idx1 in range(len(cells_in_box)):
                for idx2 in range(idx1 + 1, len(cells_in_box)):
                    constraint = NotEqualConstraint(
                        cells_in_box[idx1], 
                        cells_in_box[idx2]
                    )
                    csp.add_constraint(constraint)
    
    return csp


def generate_sudoku(difficulty: str = "expert") -> CSP:
    """
    Generate a random Sudoku puzzle with a unique solution.
    
    For expert difficulty, loads puzzles from hardest_sudoku.json using an iterator.
    Each call returns the next puzzle from the dataset (cycles indefinitely).
    For other difficulties, generates random puzzles by removing cells from a solved grid.
    
    Args:
        difficulty: Difficulty level - "easy" (40-50 clues), "medium" (30-39 clues), 
                   "hard" (25-29 clues), "expert" (17-24 clues from dataset)
        
    Returns:
        CSP instance representing the Sudoku problem
    """
    if difficulty == "expert":
        iterator = _get_expert_puzzle_iterator()
        puzzle_string = next(iterator)
        return load_sudoku_from_string(puzzle_string)
    
    difficulty_clues = {
        "easy": (40, 50),
        "medium": (30, 39),
        "hard": (25, 29)
    }
    
    min_clues, max_clues = difficulty_clues.get(difficulty, (30, 39))
    num_clues = random.randint(min_clues, max_clues)
    
    initial_grid = generate_solved_sudoku()
    
    initial_values = {}
    all_positions = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(all_positions)
    
    for pos in all_positions[:num_clues]:
        initial_values[pos] = initial_grid[pos]
    
    return create_sudoku(initial_values)


def generate_solved_sudoku() -> Dict[Tuple[int, int], int]:
    """
    Generate a valid completed Sudoku grid using a known valid base pattern.
    
    Returns:
        Dictionary mapping (row, col) -> value for a complete valid Sudoku
    """
    base_solution = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9],
        [4, 5, 6, 7, 8, 9, 1, 2, 3],
        [7, 8, 9, 1, 2, 3, 4, 5, 6],
        [2, 3, 4, 5, 6, 7, 8, 9, 1],
        [5, 6, 7, 8, 9, 1, 2, 3, 4],
        [8, 9, 1, 2, 3, 4, 5, 6, 7],
        [3, 4, 5, 6, 7, 8, 9, 1, 2],
        [6, 7, 8, 9, 1, 2, 3, 4, 5],
        [9, 1, 2, 3, 4, 5, 6, 7, 8]
    ]
    
    grid = {}
    for i in range(9):
        for j in range(9):
            grid[(i, j)] = base_solution[i][j]
    
    grid = apply_valid_permutations(grid)
    
    return grid


def apply_valid_permutations(grid: Dict[Tuple[int, int], int]) -> Dict[Tuple[int, int], int]:
    """
    Apply valid permutations to a Sudoku grid to add variety.
    
    Valid permutations that preserve Sudoku constraints:
    - Swap rows within the same band (group of 3 rows)
    - Swap columns within the same stack (group of 3 columns)
    - Permute the digits 1-9
    
    Args:
        grid: Initial valid Sudoku grid
        
    Returns:
        Transformed grid that is still valid
    """
    digits = list(range(1, 10))
    random.shuffle(digits)
    digit_map = {i+1: digits[i] for i in range(9)}
    
    new_grid = {}
    for pos, value in grid.items():
        new_grid[pos] = digit_map[value]
    
    row_mapping = {}
    for band in range(3):
        band_rows = [band * 3, band * 3 + 1, band * 3 + 2]
        shuffled_rows = band_rows.copy()
        random.shuffle(shuffled_rows)
        for old_idx, old_row in enumerate(band_rows):
            row_mapping[old_row] = shuffled_rows[old_idx]
    
    temp_grid = {}
    for (i, j), value in new_grid.items():
        new_row = row_mapping[i]
        temp_grid[(new_row, j)] = value
    new_grid = temp_grid
    
    col_mapping = {}
    for stack in range(3):
        stack_cols = [stack * 3, stack * 3 + 1, stack * 3 + 2]
        shuffled_cols = stack_cols.copy()
        random.shuffle(shuffled_cols)
        for old_idx, old_col in enumerate(stack_cols):
            col_mapping[old_col] = shuffled_cols[old_idx]
    
    temp_grid = {}
    for (i, j), value in new_grid.items():
        new_col = col_mapping[j]
        temp_grid[(i, new_col)] = value
    
    return temp_grid


def load_sudoku_from_string(puzzle_string: str) -> CSP:
    """
    Load a Sudoku puzzle from a string representation.
    
    Args:
        puzzle_string: String of 81 characters where '0' or '.' represents empty cell
                      and '1'-'9' represent filled cells. Can include whitespace/newlines.
        
    Returns:
        CSP instance representing the Sudoku problem
        
    Example:
        puzzle = '''
        5 3 0  0 7 0  0 0 0
        6 0 0  1 9 5  0 0 0
        0 9 8  0 0 0  0 6 0
        
        8 0 0  0 6 0  0 0 3
        4 0 0  8 0 3  0 0 1
        7 0 0  0 2 0  0 0 6
        
        0 6 0  0 0 0  2 8 0
        0 0 0  4 1 9  0 0 5
        0 0 0  0 8 0  0 7 9
        '''
    """

    if len(clean_string) != 81:
        raise ValueError(f"Puzzle string must have 81 digits, got {len(clean_string)}")
    
    initial_values = {}
    for i in range(9):
        for j in range(9):
            idx = i * 9 + j
            char = clean_string[idx]
            if char != '0' and char != '.':
                value = int(char)
                if 1 <= value <= 9:
                    initial_values[(i, j)] = value
    
    return create_sudoku(initial_values)


def print_sudoku(assignment: Dict[Tuple[int, int], int]) -> None:
    """
    Print a Sudoku grid in a readable format.
    
    Args:
        assignment: Dictionary mapping (row, col) -> value
    """
    print("\n" + "=" * 25)
    for i in range(9):
        if i % 3 == 0 and i != 0:
            print("-" * 25)
        
        row_str = ""
        for j in range(9):
            if j % 3 == 0 and j != 0:
                row_str += "| "
            
            cell = (i, j)
            if cell in assignment:
                row_str += str(assignment[cell]) + " "
            else:
                row_str += ". "
        
        print(row_str)
    print("=" * 25)


SAMPLE_EASY = """
5 3 0  0 7 0  0 0 0
6 0 0  1 9 5  0 0 0
0 9 8  0 0 0  0 6 0

8 0 0  0 6 0  0 0 3
4 0 0  8 0 3  0 0 1
7 0 0  0 2 0  0 0 6

0 6 0  0 0 0  2 8 0
0 0 0  4 1 9  0 0 5
0 0 0  0 8 0  0 7 9
"""

SAMPLE_MEDIUM = """
0 0 0  6 0 0  4 0 0
7 0 0  0 0 3  6 0 0
0 0 0  0 9 1  0 8 0

0 0 0  0 0 0  0 0 0
0 5 0  1 8 0  0 0 3
0 0 0  3 0 6  0 4 5

0 4 0  2 0 0  0 6 0
9 0 3  0 0 0  0 0 0
0 2 0  0 0 0  1 0 0
"""

SAMPLE_HARD = """
0 0 0  0 0 0  0 1 2
0 0 0  0 0 0  0 0 3
0 0 2  3 0 0  4 0 0

0 0 1  8 0 0  0 0 5
0 6 0  0 7 0  8 0 0
0 0 0  0 0 9  0 0 0

0 0 8  5 0 0  0 0 0
9 0 0  0 4 0  5 0 0
4 7 0  0 0 6  0 0 0
"""

EXPERT_PUZZLES = [
    """
    0 0 0  0 0 0  0 0 0
    0 0 0  0 0 3  0 8 5
    0 0 1  0 2 0  0 0 0
    
    0 0 0  5 0 7  0 0 0
    0 0 4  0 0 0  1 0 0
    0 9 0  0 0 0  0 0 0
    
    5 0 0  0 0 0  0 7 3
    0 0 2  0 1 0  0 0 0
    0 0 0  0 4 0  0 0 9
    """,
    """
    0 0 5  3 0 0  0 0 0
    8 0 0  0 0 0  0 2 0
    0 7 0  0 1 0  5 0 0
    
    4 0 0  0 0 5  3 0 0
    0 1 0  0 7 0  0 0 6
    0 0 3  2 0 0  0 8 0
    
    0 6 0  5 0 0  0 0 9
    0 0 4  0 0 0  0 3 0
    0 0 0  0 0 9  7 0 0
    """,
    """
    0 0 0  7 0 0  0 0 0
    1 0 0  0 0 0  0 0 0
    0 0 0  4 3 0  2 0 0
    
    0 0 0  0 0 0  0 0 6
    0 0 0  5 0 9  0 0 0
    0 0 0  0 0 0  4 1 8
    
    0 0 0  0 8 1  0 0 0
    0 0 2  0 0 0  0 5 0
    0 4 0  0 0 0  3 0 0
    """,
    """
    0 0 0  0 0 0  0 1 0
    0 0 0  0 0 2  0 0 3
    0 0 0  4 0 0  0 0 0
    
    0 0 0  0 0 3  0 5 6
    0 0 0  0 0 0  0 0 0
    0 0 1  0 0 0  0 0 0
    
    5 0 0  0 0 0  0 0 8
    0 0 0  0 9 0  0 0 0
    2 0 0  0 0 0  0 0 0
    """,
    """
    8 0 0  0 0 0  0 0 0
    0 0 3  6 0 0  0 0 0
    0 7 0  0 9 0  2 0 0
    
    0 5 0  0 0 7  0 0 0
    0 0 0  0 4 5  7 0 0
    0 0 0  1 0 0  0 3 0
    
    0 0 1  0 0 0  0 6 8
    0 0 8  5 0 0  0 1 0
    0 9 0  0 0 0  4 0 0
    """,
    """
    0 0 0  0 0 0  6 8 0
    0 0 0  0 7 3  0 0 9
    3 0 9  0 0 0  0 4 5
    
    4 9 0  0 0 0  0 0 0
    8 0 3  0 5 0  9 0 2
    0 0 0  0 0 0  0 3 6
    
    9 6 0  0 0 0  3 0 8
    7 0 0  6 8 0  0 0 0
    0 2 8  0 0 0  0 0 0
    """,
    """
    0 0 0  0 0 0  0 0 0
    0 0 0  0 0 0  0 0 1
    0 0 0  0 0 2  3 4 5
    
    0 0 0  0 6 7  8 9 0
    0 0 0  1 0 0  0 0 0
    0 2 3  4 5 0  0 0 0
    
    6 7 8  9 0 0  0 0 0
    9 0 0  0 0 0  0 0 0
    0 0 0  0 0 0  0 0 0
    """,
    """
    0 0 6  0 0 8  5 0 0
    0 0 0  0 0 0  0 4 0
    7 0 0  0 0 0  0 0 1
    
    0 5 0  0 0 0  0 0 0
    0 0 0  6 1 0  0 0 0
    0 0 0  0 0 0  3 0 0
    
    4 0 0  0 0 9  0 0 0
    0 3 0  0 5 0  0 0 0
    0 0 7  2 0 0  0 0 0
    """,
    """
    0 0 0  1 0 5  0 0 0
    1 4 0  0 0 0  6 7 0
    0 8 0  0 0 2  4 0 0
    
    0 0 0  0 7 0  0 0 5
    0 0 0  0 0 0  0 0 0
    4 0 0  0 1 0  0 0 0
    
    0 0 3  5 0 0  0 0 0
    0 2 8  0 0 0  0 0 0
    0 0 0  4 0 9  0 0 0
    """,
    """
    0 0 1  0 0 0  0 0 0
    2 0 0  0 8 0  3 0 0
    0 0 0  7 0 0  0 1 0
    
    0 7 0  0 0 0  0 0 8
    0 0 0  6 0 2  0 0 0
    8 0 0  0 0 0  0 4 0
    
    0 6 0  0 0 5  0 0 0
    0 0 4  0 7 0  0 0 1
    0 0 0  0 0 0  5 0 0
    """
]
