import socketio
import time

# Create a Socket.IO client instance
sio = socketio.Client()

@sio.event
def connect():
    print("✅ Connection to server established.")

@sio.on('alert_data', namespace='/live_feed')
def on_alert_data(data):
    """
    This function is triggered when the server sends an 'alert_data' event.
    """
    print("\n--- 📡 Broadcast Received! ---")
    print(f"Received {len(data)} alerts.")
    
    # Example: Print the headline of each alert
    for i, alert in enumerate(data):
        headline = alert.get('headline', 'No Headline Provided')
        print(f"  {i+1}. {headline}")
    print("-----------------------------\n")

@sio.event
def disconnect():
    print("🔌 Disconnected from server.")

if __name__ == '__main__':
    # **CRITICAL STEP:** Replace this with the actual IP address of the Flask server from IT.
    SERVER_IP = "YOUR_FLASK_SERVER_IP"
    
    server_address = f'http://{SERVER_IP}:5000'
    
    try:
        print(f"Attempting to connect to {server_address} in the /live_feed namespace...")
        sio.connect(server_address, namespaces=['/live_feed'])
        sio.wait()
    except socketio.exceptions.ConnectionError as e:
        print(f"❌ ConnectionError: Could not connect to the server at {server_address}.")
        print("   Please ensure the server is running and you have replaced 'YOUR_FLASK_SERVER_IP' with the correct IP address.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")