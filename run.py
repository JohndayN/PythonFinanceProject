import subprocess
import os
import sys
import time
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import config

def check_dependencies():
    required_packages = [
        'fastapi', 'uvicorn', 'pandas', 'numpy', 'pymongo',
        'sklearn', 'torch', 'vnstock', 'pdfplumber', 'yfinance', 'streamlit',
    ]
    
    print("Checking dependencies...")
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Run: pip install -r requirements_new.txt")
        return False
    
    print("All dependencies installed")
    return True

def start_python_api():
    """Start the Python FastAPI server"""
    print("\nStarting Python FastAPI server...")
    print(f"Running on: http://localhost:8000")
    print(f"Docs: http://localhost:8000/docs")
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "api:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))
    return process

def start_nodejs_backend():
    """Start the Node.js proxy server"""
    print("\nStarting Node.js backend server...")
    print(f"Running on: http://localhost:3000")
    
    backend_dir = PROJECT_ROOT / "BackEnd"
    
    # Find npm executable
    npm_path = shutil.which("npm")
    if not npm_path:
        print("   Warning: npm not found in PATH. Skipping Node.js backend.")
        return None
    
    # Check if node_modules exist
    if not (backend_dir / "node_modules").exists():
        print("   Installing Node.js dependencies...")
        env = os.environ.copy()
        npm_install = subprocess.run([npm_path, "install"], cwd=str(backend_dir), capture_output=True, env=env)
        if npm_install.returncode != 0:
            print(f"   Error installing dependencies: {npm_install.stderr.decode()}")
            return None
    
    env = os.environ.copy()
    env["CI"] = "true"  # Disable interactive mode
    process = subprocess.Popen([npm_path, "start"], cwd=str(backend_dir), env=env)
    return process

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("\nStarting Streamlit Dashboard...")
    print(f"Running on: http://localhost:8501")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run",
        "DashBoard/app.py"
    ]
    
    process = subprocess.Popen(cmd, cwd=str(PROJECT_ROOT))
    return process

def start_frontend():
    """Start the React frontend development server"""
    print("\nStarting React Frontend...")
    print(f"Running on: http://localhost:3001")
    
    frontend_dir = PROJECT_ROOT / "FrontEnd"
    
    # Check if frontend exists
    if not frontend_dir.exists():
        print("Warning: FrontEnd folder not found. Skipping frontend.")
        return None
    
    # Find npm
    npm_path = shutil.which("npm")
    if not npm_path:
        print("Warning: npm not found. Skipping frontend.")
        return None
    
    # Check if node_modules exist
    if not (frontend_dir / "node_modules").exists():
        print("   Installing frontend dependencies...")
        env = os.environ.copy()
        npm_install = subprocess.run([npm_path, "install"], cwd=str(frontend_dir), capture_output=True, env=env)
        if npm_install.returncode != 0:
            print(f"   Error installing dependencies: {npm_install.stderr.decode()}")
            return None
    
    env = os.environ.copy()
    env["REACT_APP_API_URL"] = "http://localhost:8000"
    env["CI"] = "true"  # Disable interactive mode
    process = subprocess.Popen([npm_path, "start"], cwd=str(frontend_dir), env=env)
    return process

def main():
    """Main startup function"""
    print("\n" + "="*60)
    print("Finance Application - Startup Manager")
    print("="*60 + "\n")
    
    # Start with dependency check
    if not check_dependencies():
        sys.exit(1)
    
    processes = []
    
    try:
        # Start Python API
        python_process = start_python_api()
        if python_process:
            processes.append(("Python API", python_process))
        
        # Wait for Python API to start
        time.sleep(3)
        
        # Start Node.js backend
        nodejs_process = start_nodejs_backend()
        if nodejs_process:
            processes.append(("Node.js Backend", nodejs_process))
        
        time.sleep(2)
        
        # Start React frontend
        frontend_process = start_frontend()
        if frontend_process:
            processes.append(("React Frontend", frontend_process))
        
        time.sleep(2)
        
        # Start Streamlit (optional)
        if "--dashboard" in sys.argv:
            dashboard_process = start_dashboard()
            if dashboard_process:
                processes.append(("Streamlit Dashboard", dashboard_process))
        
        print("\n" + "="*60)
        print("All services started successfully!")
        print("="*60)
        print("\nServices running:")
        print("Python API: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs")
        if nodejs_process:
            print("Node.js Backend: http://localhost:3000")
        print("React Frontend: http://localhost:3001")
        
        if "--dashboard" in sys.argv:
            print("Streamlit Dashboard: http://localhost:8501")
        
        print("\nPress Ctrl+C to stop all services...\n")
        
        # Keep running
        for name, process in processes:
            process.wait()
    
    except KeyboardInterrupt:
        print("\n\nShutting down services...")
        for name, process in processes:
            print(f"  Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print("All services stopped")
    
    except Exception as e:
        print(f"\nError: {e}")
        # Clean up on error
        for name, process in processes:
            process.terminate()
            process.kill()
        sys.exit(1)

if __name__ == "__main__":
    main()
