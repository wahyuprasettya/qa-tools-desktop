import re

text = """benerin ketika data dari chat gpt seperti ini | Focus | Type | ID |
| --- | --- | --- |
| Client | Functional | TC-001 |"""

for line in text.splitlines():
    if "|" not in line: continue
    
    # Let's see what happens if we find the first and last pipe
    first_pipe = line.find("|")
    last_pipe = line.rfind("|")
    
    print(f"Line: {line}")
    print(f"First pipe index: {first_pipe}, Last pipe index: {last_pipe}")
    
