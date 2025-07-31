import re
import sys


def fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Fix E302: Add two blank lines before class definition
    for i in range(len(lines)):
        if lines[i].startswith('class '):
            # Find the first non-empty line before the class
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            # Insert two blank lines if needed
            if i - j < 3:  # Less than 2 blank lines before class
                lines.insert(i, '\n' * (3 - (i - j)))
                break  # Break after first class to avoid shifting indices

    # Fix W293: Remove whitespace from blank lines
    lines = [line if line.strip() else '\n' for line in lines]

    # Write the fixed content back to the file
    with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
        f.writelines(lines)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        fix_file(sys.argv[1])
    else:
        print("Usage: python fix_lint.py <file_path>")
