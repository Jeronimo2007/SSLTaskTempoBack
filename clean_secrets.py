#!/usr/bin/env python3
import re
import sys
import os

def clean_file_content(content):
    """
    Clean sensitive data from file content by replacing hardcoded credentials
    with environment variable references.
    """
    # Replace Google Client ID with environment variable
    content = re.sub(
        r'GOOGLE_CLIENT_ID\s*=\s*"[^"]*"',
        'GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")',
        content
    )
    
    # Replace Google Client Secret with environment variable
    content = re.sub(
        r'GOOGLE_CLIENT_SECRET\s*=\s*"[^"]*"',
        'GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")',
        content
    )
    
    # Also replace any REDIRECT_URI with environment variable call if it's hardcoded
    content = re.sub(
        r'REDIRECT_URI\s*=\s*"https://ssl\.tasktempos\.com/auth/callback/google"',
        'REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "https://ssl.tasktempos.com/auth/callback/google")',
        content
    )
    
    # Ensure 'os' is imported if it's not already
    if 'import os' not in content and 'from os import' not in content:
        # Add import after other imports
        lines = content.split('\n')
        import_added = False
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                if i + 1 < len(lines) and (not lines[i+1].startswith('import ') and not lines[i+1].startswith('from ')):
                    lines.insert(i + 1, 'import os')
                    import_added = True
                    break
        
        # If no imports were found or no suitable place to add import
        if not import_added:
            lines.insert(0, 'import os')
        
        content = '\n'.join(lines)
    
    return content

def process_file(file_path):
    """Process a single file, cleaning sensitive data."""
    # Only process google_auth.py file
    if not file_path.endswith('app/routes/google_auth.py'):
        return
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        sys.stderr.write(f"Error reading {file_path}: {e}\n")
        return
    
    # Clean the content
    cleaned_content = clean_file_content(content)
    
    # Write back to file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
    except Exception as e:
        sys.stderr.write(f"Error writing to {file_path}: {e}\n")

def main():
    """Main function to process files."""
    if len(sys.argv) > 1:
        for file_path in sys.argv[1:]:
            process_file(file_path)
    else:
        sys.stderr.write("No files provided to process.\n")

if __name__ == "__main__":
    main()

