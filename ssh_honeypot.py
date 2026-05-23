#!/usr/bin/env python3
"""
Minimal SSH Honeypot for LLM-Enhanced Deception Research
Captures login attempts, commands, and session behaviour
"""

import socket
import threading
import json
import os
from datetime import datetime
from pathlib import Path

class SSHHoneypot:
    def __init__(self, host='127.0.0.1', port=2222):
        self.host = host
        self.port = port
        self.session_counter = 0
        self.log_dir = Path('honeypot_logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # Banner that looks like a real SSH server
        self.banner = b"SSH-2.0-OpenSSH_7.4\r\n"
        
    def start(self):
        """Start the honeypot server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        print(f"🍯 Honeypot listening on {self.host}:{self.port}")
        print(f"📁 Logs will be saved to: {self.log_dir.absolute()}")
        
        try:
            while True:
                client_socket, client_address = server_socket.accept()
                self.session_counter += 1
                
                # Handle each connection in a separate thread
                thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address, self.session_counter)
                )
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print("\n⛔ Honeypot stopped.")
        finally:
            server_socket.close()
    
    def handle_client(self, client_socket, client_address, session_id):
        """Handle a single client connection"""
        session_log = {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'client_ip': client_address[0],
            'client_port': client_address[1],
            'events': []
        }
        
        try:
            # Send banner
            client_socket.send(self.banner)
            session_log['events'].append({
                'time': datetime.now().isoformat(),
                'event': 'banner_sent',
                'data': self.banner.decode().strip()
            })
            
            # Simulate SSH protocol exchange
            # In a real scenario, we'd do full key exchange
            # For now, we'll just accept username/password attempts
            
            client_socket.settimeout(5)
            
            while True:
                try:
                    # Receive data from client
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Log the attempt
                    session_log['events'].append({
                        'time': datetime.now().isoformat(),
                        'event': 'data_received',
                        'data': data[:100].decode('utf-8', errors='ignore')  # First 100 chars
                    })
                    
                    # Try to extract username/password (very simplistic)
                    try:
                        attempt_str = data.decode('utf-8', errors='ignore').strip()
                        if 'root' in attempt_str.lower() or 'admin' in attempt_str.lower():
                            session_log['events'].append({
                                'time': datetime.now().isoformat(),
                                'event': 'credential_attempt_detected',
                                'data': attempt_str[:50]
                            })
                    except:
                        pass
                    
                    # Send a fake error response
                    response = b"Permission denied (publickey,password).\r\n"
                    client_socket.send(response)
                    
                except socket.timeout:
                    break
                except Exception as e:
                    session_log['events'].append({
                        'time': datetime.now().isoformat(),
                        'event': 'error',
                        'data': str(e)
                    })
                    break
        
        except Exception as e:
            session_log['events'].append({
                'time': datetime.now().isoformat(),
                'event': 'connection_error',
                'data': str(e)
            })
        
        finally:
            # Save session log
            log_file = self.log_dir / f"session_{session_id:04d}.json"
            with open(log_file, 'w') as f:
                json.dump(session_log, f, indent=2)
            
            session_log['events'].append({
                'time': datetime.now().isoformat(),
                'event': 'session_closed',
                'data': f'Total events: {len(session_log["events"])}'
            })
            
            # Also save to a master log
            master_log = self.log_dir / 'master_log.jsonl'
            with open(master_log, 'a') as f:
                f.write(json.dumps(session_log) + '\n')
            
            client_socket.close()
            print(f"📝 Session {session_id} from {client_address[0]} logged")

if __name__ == '__main__':
    honeypot = SSHHoneypot(host='127.0.0.1', port=2222)
    honeypot.start()
