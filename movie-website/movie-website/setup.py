import sys
import os
import subprocess

print("=" * 60)
print("          NETBOX MOVIE WEBSITE SETUP")
print("=" * 60)

# Fix Python path
sys.path.insert(0, r'D:\Lib\site-packages')

# Try to install minimal packages
packages = ["flask", "flask-cors", "gunicorn"]

print("\n Installing packages...")
for package in packages:
    print(f"\nInstalling {package}...")
    
    # Method 1: Try pip module
    try:
        import pip
        pip.main(['install', package])
        print(f"✅ {package} installed via pip module")
        continue
    except:
        pass
    
    # Method 2: Try subprocess
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "install", package], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {package} installed via subprocess")
        else:
            print(f"⚠️  Failed: {result.stderr[:100]}")
    except:
        print(f" Could not install {package}")

print("\n" + "=" * 60)
print("Verifying installation...")

# Check what's installed
try:
    import flask
    print(f" Flask: {flask.__version__}")
except:
    print(" Flask not installed")

try:
    from flask_cors import CORS
    print(" Flask-CORS: Installed")
except:
    print(" Flask-CORS not installed")

print("\n" + "=" * 60)
print("Creating required folders...")

# Create folders
folders = ["backend/movies", "static/assets"]
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f" Created: {folder}")

print("\n" + "=" * 60)
print(" SETUP COMPLETE!")
print("\nTo run your website:")
print("1. cd backend")
print("2. python app.py")
print("3. Open: http://localhost:5000")
print("=" * 60)

input("\nPress Enter to exit...")
