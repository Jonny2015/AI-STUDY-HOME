import re
from pathlib import Path

app_dir = Path("app")
for py_file in app_dir.rglob("*.py"):
    content = py_file.read_text()
    
    # Check what types are used
    uses_list = bool(re.search(r'\bList\[', content))
    uses_dict = bool(re.search(r'\bDict\[', content))
    
    if uses_list or uses_dict:
        # Check current typing import
        typing_match = re.search(r'from typing import ([^\n]+)', content)
        current_imports = typing_match.group(1) if typing_match else ""
        
        needed = []
        if uses_list and 'List' not in current_imports:
            needed.append('List')
        if uses_dict and 'Dict' not in current_imports:
            needed.append('Dict')
        
        if needed:
            print(f"{py_file}: needs {needed}")
