import os
import subprocess
import time
import sys
import threading
import signal

def start_api_server():
    """Start the FastAPI server"""
    print("Starting API server...")
    api_process = subprocess.Popen([sys.executable, "api.py"])
    return api_process

def start_gradio_interface():
    """Start the Gradio interface"""
    print("Starting Gradio interface...")
    gradio_process = subprocess.Popen([sys.executable, "app.py"])
    return gradio_process

def shutdown(api_process, gradio_process):
    """Shutdown all processes"""
    print("\nShutting down...")
    if api_process:
        api_process.terminate()
    if gradio_process:
        gradio_process.terminate()
    
    # Wait for processes to terminate
    if api_process:
        api_process.wait()
    if gradio_process:
        gradio_process.wait()
        
    print("All processes terminated.")

def main():
    """Main function to start all components"""
    print("Starting Pronunciation Practice System...")
    
    # Start API server
    api_process = start_api_server()
    
    # Wait for API server to start up
    print("Waiting for API server to start...")
    time.sleep(5)
    
    # Start Gradio interface
    gradio_process = start_gradio_interface()
    
    # Handle CTRL+C gracefully
    def signal_handler(sig, frame):
        shutdown(api_process, gradio_process)
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    print("\nPronunciation Practice System is running!")
    print("Press CTRL+C to shutdown.")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown(api_process, gradio_process)

if __name__ == "__main__":
    main() 