"""
DupeFinder ML Engine - Environment Setup Script
Task 2.1: Automated ML environment setup and verification

This script will:
1. Check Python version
2. Install required dependencies
3. Run verification tests
"""

import subprocess
import sys
import os

def check_python_version():
    """Verify Python version is 3.8+"""
    print("=" * 60)
    print("Checking Python Version")
    print("=" * 60)
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required!")
        return False
    
    print("✓ Python version is compatible\n")
    return True


def install_dependencies():
    """Install ML engine dependencies"""
    print("=" * 60)
    print("Installing Dependencies")
    print("=" * 60)
    print("This may take several minutes...\n")
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        
        # Install dependencies
        print("\nInstalling ML engine dependencies...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        
        print("\n✓ Dependencies installed successfully!\n")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing dependencies: {e}")
        return False


def run_verification_tests():
    """Run setup verification tests"""
    print("=" * 60)
    print("Running Verification Tests")
    print("=" * 60)
    print()
    
    try:
        result = subprocess.call([sys.executable, "test_setup.py"])
        return result == 0
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False


def main():
    """Main setup workflow"""
    print("\n" + "=" * 60)
    print("DupeFinder ML Engine - Automated Setup")
    print("=" * 60 + "\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Ask user to confirm installation
    print("This will install the following packages:")
    print("  - PyTorch (torch, torchvision)")
    print("  - Image processing (Pillow, opencv-python)")
    print("  - ML libraries (numpy, pandas, scikit-learn, scipy)")
    print("  - Utilities (yaml, matplotlib, pytest)")
    print()
    
    response = input("Proceed with installation? (y/n): ").strip().lower()
    if response != 'y':
        print("Setup cancelled.")
        sys.exit(0)
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed during dependency installation!")
        sys.exit(1)
    
    # Run verification tests
    print("\nDependencies installed. Running verification tests...\n")
    if not run_verification_tests():
        print("\n❌ Setup verification failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("🎉 ML Engine Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Task 2.2: Create image preprocessing pipeline")
    print("  2. Task 2.3: Implement feature extraction")
    print("  3. Task 2.4: Implement similarity calculation")
    print()


if __name__ == "__main__":
    main()









