import socket
import time
import cv2
from datetime import datetime
from colorama import Fore
from src.recognition import process_detected_face
from src.database_handler import log_user_attendance
from src.camera_utils import handle_camera_failure

def run_attendance_service(stop_event, caps, camera_indices, app_insight, host_ip='0.0.0.0', port=65432):
    """
    Main loop for the Attendance Unit functionality.
    """
    # 1. Setup Socket Server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host_ip, port))
    server_socket.listen(1)
    server_socket.settimeout(1.0) # check stop_event every 1s

    print(Fore.CYAN + f"Attendance Unit Ready. Listening on Port {port}...")
    
    # 2. Select Camera (Index 1 is standard for Attendance in your setup)
    active_cam_idx = camera_indices[0]
    last_alert_time = 0 

    while not stop_event.is_set():
        try:
            # --- Wait for Connection ---
            try:
                client_socket, addr = server_socket.accept()
            except socket.timeout:
                continue # Loop back to check stop_event

            print(Fore.YELLOW + f"Connection from {addr}. Starting Attendance Scan...")

            # Optional: Read trigger message
            try:
                client_socket.settimeout(2.0)
                msg = client_socket.recv(1024).decode().strip()
                if msg != "TRIGGER":
                    client_socket.close()
                    continue
            except:
                pass 

            # --- Start Scanning Loop ---
            known_face_found = False
            scan_duration = 15 # Scans for 15 seconds
            scan_start_time = time.time()
            detected_name = "Unknown"
            
            while (time.time() - scan_start_time < scan_duration):
                # Check for global stop
                if stop_event.is_set():
                    break

                # Safety check
                if len(caps) <= active_cam_idx:
                    print(f"Error: Attendance Camera Index {active_cam_idx} out of range.")
                    time.sleep(1)
                    break

                ret, frame = caps[active_cam_idx].read()
                
                # --- CAMERA FAILURE HANDLING ---
                if not ret:
                    # Pass stop_event so we can cancel during recovery
                    recovered_cap = handle_camera_failure(caps[active_cam_idx], active_cam_idx, stop_event)
                    
                    if recovered_cap is None:
                        # User pressed Ctrl+C during recovery
                        stop_event.set()
                        break 
                    
                    caps[active_cam_idx] = recovered_cap
                    continue

                Faces = app_insight.get(frame)
                
                for face in Faces:
                    # 'task_queue' is None here as per your design
                    last_alert_time, AnomalyDetected, Labels = process_detected_face(
                        frame, face, None, last_alert_time, purpose='attendence'
                    )

                    if not AnomalyDetected:
                        # SUCCESS: Log and Confirm
                        attendenceTime = datetime.now().strftime('%Y%m%d_%H%M%S')
                        log_user_attendance(Labels)
                        print(Fore.GREEN + f"Valid User Found: {Labels} at {attendenceTime}")
                        
                        detected_name = Labels
                        known_face_found = True
                        
                        # Visual Feedback
                        cv2.putText(frame, f"Welcome {Labels}!", (50, 50), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                        cv2.imshow("Attendance Scan", frame)
                        cv2.waitKey(1)
                        
                        time.sleep(1.0) # Small pause to show success message
                        break # Break face loop
                
                # Show Feed
                cv2.imshow("Attendance Scan", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    stop_event.set()
                    break
                
                if known_face_found:
                    break

            # --- Send Response ---
            print(Fore.CYAN + f"Session Ended. Sending: {detected_name}")
            try:
                client_socket.sendall((detected_name + "\n").encode('utf-8'))
                client_socket.close()
            except Exception as e:
                print(f"Error sending data: {e}")

            # Close window after scan finishes to keep desktop clean
            try:
                cv2.destroyWindow("Attendance Scan")
            except:
                pass
            
            print(Fore.CYAN + "Attendance Check Complete. Idle.")

        except Exception as e:
            print(f"Service Error: {e}")
            time.sleep(1)
    
    server_socket.close()
    print("Attendance Service Stopped.")