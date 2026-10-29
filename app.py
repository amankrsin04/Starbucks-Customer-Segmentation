"""
Root Application Entry Point
Forwards execution to Starbucks_Customer_Segmentation-main/app.py
"""
import sys
import os
import importlib.util

inner_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Starbucks_Customer_Segmentation-main")
os.chdir(inner_dir)
if inner_dir not in sys.path:
    sys.path.insert(0, inner_dir)

inner_app_path = os.path.join(inner_dir, "app.py")
spec = importlib.util.spec_from_file_location("starbucks_inner_app", inner_app_path)
module = importlib.util.module_from_spec(spec)
sys.modules["starbucks_inner_app"] = module
spec.loader.exec_module(module)
app = module.app

if __name__ == "__main__":
    print("\n☕ Starting Starbucks Customer Intelligence Platform...")
    print("⚡ Puture-Inspired Cyber-Studio UI Active")
    print("🌐 Access Application at: http://127.0.0.1:5000\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
