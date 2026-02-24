"""
Flask Web Application for Nifty Midcap Trend Analyzer
"""

from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from Analyzer import *
import threading
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Global expiry variable
expiry = '24-Feb-2026'

def transmit_analysis():
    """Threaded function to continuously analyze and emit data"""
    global expiry
    while True:
        try:
            # Fetch data
            data = fetch_midcap_option_chain(expiry)
            # Analyze
            analyzer = MidcapTrendAnalyzer(data)
            result = analyzer.generate_composite_signal()
            # Emit to all connected clients
            socketio.emit('analysis_data', result)
            print("Emitted analysis data")
        except Exception as e:
            print(f"Error in analysis: {e}")
            print(e)
            socketio.emit('error', {'message': str(e)})
        
        # Wait before next analysis
        time.sleep(15)# Adjust interval as needed

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('new_index.html')

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'msg': 'Connected to Nifty Midcap Trend Analyzer'})
    emit('current_expiry', {'expiry': expiry})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('change_expiry')
def handle_change_expiry(data):
    """Handle expiry change"""
    global expiry
    expiry = data['expiry']
    print(f"Expiry changed to {expiry}")
    emit('expiry_changed', {'expiry': expiry})

if __name__ == '__main__':
    # Start the analysis thread
    threading.Thread(target=transmit_analysis, daemon=True).start()
    socketio.run(app, host='127.0.0.1', port=8000, debug=True)