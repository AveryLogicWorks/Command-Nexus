import os

keywords = ['ANNUAL', 'annual', '$50', '50/yr', 'Trial:', 'Starter:', 'Pro:', 'Unlimited:']
for root, _, files in os.walk('A:/Command_Nexus/src'):
    for f in files:
        if not f.endswith('.py'):
            continue
        path = os.path.join(root, f)
        text = open(path, 'r', encoding='utf-8').read()
        found = False
        for i, line in enumerate(text.split('\n'), 1):
            if any(k in line for k in keywords):
                if not found:
                    print(path)
                    found = True
                print(f'  {i}: {line.strip()}')
        if found:
            print()
