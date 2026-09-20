import re

with open('frontend/templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '<section' in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
    elif '<h2' in line:
        print(f"   Line {i+1} [H2]: {line.strip()[:100]}")
