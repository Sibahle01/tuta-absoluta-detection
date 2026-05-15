import socket
import json
import time

UDP_IP = '192.168.7.2'
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Simulate pest outbreak over 60 seconds
for i in range(60):
    if i < 15:
        pest_count = 0
    elif i < 30:
        pest_count = 2
    elif i < 45:
        pest_count = 5
    else:
        pest_count = 8
    
    data = json.dumps({'pest_count': pest_count, 'timestamp': time.time()})
    sock.sendto(data.encode(), (UDP_IP, UDP_PORT))
    print(f"Sent: {pest_count} pests")
    time.sleep(1)

print("✅ Simulation complete")