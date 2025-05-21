"""
Run this script before running tests if you have SQLAlchemy import issues.
This temporarily downgrades SQLAlchemy to a compatible version.
"""
import subprocess
import sys

def fix_sqlalchemy():
    print("Temporarily fixing SQLAlchemy version...")
    subprocess.check_call([
        sys.executable, "-m", "pip", "install", "sqlalchemy==1.4.49"
    ])
    print("SQLAlchemy downgraded to 1.4.49 for compatibility")

if __name__ == "__main__":
    fix_sqlalchemy()
    print("You can now run your tests with: python -m pytest tests/ -v")
