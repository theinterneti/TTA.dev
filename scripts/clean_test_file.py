"""Clean up the generated test file by removing orphaned try/except blocks."""

import re

# Read the file
with open("packages/tta-dev-primitives/tests/performance/test_cache_primitive_comprehensive.py") as f:
    content = f.read()

# Remove orphaned except blocks (except without try)
# Pattern: except Exception as e: followed by print statements
pattern = r'\nexcept Exception as e:\n    print\(f"Error occurred: \{e\}"\)\n    print\("Implementing error handling based on learned strategies"\)'
content = re.sub(pattern, '', content)

# Remove orphaned try: statements (try without body)
# Pattern: standalone try: at the beginning of a line
lines = content.split('\n')
cleaned_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    # Check if this is a standalone try: statement
    if line.strip() == 'try:':
        # Look ahead to see if the next line is also try: or is not indented
        if i + 1 < len(lines):
            next_line = lines[i + 1]
            # Skip this try: if the next line is also try: or is not indented properly
            if next_line.strip() == 'try:' or (next_line and not next_line.startswith('    ') and not next_line.startswith('\t')):
                i += 1
                continue
        # Also skip if this is the last line
        elif i + 1 >= len(lines):
            i += 1
            continue
    
    cleaned_lines.append(line)
    i += 1

content = '\n'.join(cleaned_lines)

# Write back
with open("packages/tta-dev-primitives/tests/performance/test_cache_primitive_comprehensive.py", 'w') as f:
    f.write(content)

print("✅ File cleaned successfully!")
print(f"Removed orphaned try/except blocks")

