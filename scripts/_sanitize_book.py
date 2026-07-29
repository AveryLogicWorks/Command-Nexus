#!/usr/bin/env python3
"""Completely sanitize all Book references in GitHub copy - CUSTOMER FACING ONLY"""
import os
import re

FILES_TO_SANITIZE = [
    'src/parts/book/book_window.py',
    'src/parts/forge/forge_window.py', 
    'src/parts/visibility/visibility_window.py',
    'src/main.py',
]

# Replace in strings and comments - NOT class/variable names that break code
STRING_REPLACEMENTS = [
    # UI strings - aggressive replacement
    ('The Book', 'Knowledge'),
    ('the Book', 'the Knowledge'),
    ('AI Book', 'AI Knowledge'),
    ('Open Book', 'Open Knowledge'),
    ('its Book', 'its Knowledge'),
    ('Book for AI', 'Knowledge for AI'),
    ('Save Book', 'Save Knowledge'),
    ('Talk to Book Keeper', 'Talk to Knowledge Keeper'),
    ('Talk to Intelligence Guide', 'Talk to Knowledge Guide'),
    ('No Book Loaded', 'No Knowledge Loaded'),
    ('Book (Compendium of Truth)', 'Knowledge System'),
    ('Book structure', 'Knowledge structure'),
    ('Book content', 'Knowledge content'),
    ('Book defaults', 'Knowledge defaults'),
    ('Book window', 'Knowledge window'),
    ('screen Book', 'screen Knowledge'),
    ('Per-AI Book', 'Per-AI Knowledge'),
    ('screen Intelligence', 'screen Knowledge'),
    ('Intelligence content', 'Knowledge content'),
    ('Intelligence Guide', 'Knowledge Guide'),
    ('Intelligence for AI', 'Knowledge for AI'),
    ('Save Intelligence', 'Save Knowledge'),
    ('No Intelligence Loaded', 'No Knowledge Loaded'),
    ('AI Intelligence', 'AI Knowledge'),
]

def sanitize_file(filepath):
    full_path = os.path.join(r'B:\Documents\GitHub\Command Nexus', filepath)
    if not os.path.exists(full_path):
        print(f"SKIP: {filepath} (not found)")
        return
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Replace all string occurrences
    for old, new in STRING_REPLACEMENTS:
        content = content.replace(old, new)
    
    if content != original:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"SANITIZED: {filepath}")
    else:
        print(f"CLEAN: {filepath}")

if __name__ == '__main__':
    print("=" * 60)
    print("SANITIZING BOOK REFERENCES - GITHUB COPY ONLY")
    print("=" * 60)
    for filepath in FILES_TO_SANITIZE:
        sanitize_file(filepath)
    print("=" * 60)
    print("DONE - All customer-facing Book references sanitized")
