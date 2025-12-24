import socket

# Configuration
DOOR_PORT = 4210
# Broadcast IP ensures it reaches the ESP32 regardless of its specific IP
BROADCAST_IP = "255.255.255.255"

def open_remote_door():
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Enable Broadcast
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Send "OPEN" command
        message = b"OPEN"
        sock.sendto(message, (BROADCAST_IP, DOOR_PORT))
        print(f"[Door Control] Sent OPEN signal to {BROADCAST_IP}:{DOOR_PORT}")
        
        sock.close()
    except Exception as e:
        print(f"[Door Control] Failed to send command: {e}")

if __name__ == "__main__":
    # Test execution
    open_remote_door()