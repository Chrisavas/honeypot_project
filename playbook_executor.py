#!/usr/bin/env python3
"""
Controlled Attacker Playbooks
Simulates various attacker behaviors in isolated environment
"""

import socket
import time
import json
import random
from datetime import datetime
from pathlib import Path

class AttackerPlaybook:
    def __init__(self, playbook_name, target_host='127.0.0.1', target_port=2222):
        self.name = playbook_name
        self.target_host = target_host
        self.target_port = target_port
        self.commands = []
        self.start_time = None
        self.end_time = None
    
    def add_command(self, cmd, delay=0.5):
        """Add a command to the playbook with optional delay"""
        self.commands.append({'cmd': cmd, 'delay': delay})
    
    def execute(self):
        """Execute the playbook against the honeypot"""
        self.start_time = datetime.now()
        session_data = {
            'playbook': self.name,
            'start_time': self.start_time.isoformat(),
            'commands_executed': []
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.target_host, self.target_port))
            
            # Read the banner
            banner = sock.recv(1024)
            session_data['banner'] = banner.decode('utf-8', errors='ignore').strip()
            
            # Execute each command
            for cmd_data in self.commands:
                cmd = cmd_data['cmd']
                delay = cmd_data['delay']
                
                # Send command
                sock.send(cmd.encode() + b'\r\n')
                session_data['commands_executed'].append({
                    'timestamp': datetime.now().isoformat(),
                    'command': cmd
                })
                
                # Receive response
                try:
                    sock.settimeout(2)
                    response = sock.recv(1024)
                    session_data['commands_executed'][-1]['response'] = response.decode('utf-8', errors='ignore')[:200]
                except:
                    pass
                
                # Delay between commands
                time.sleep(delay)
            
            sock.close()
        
        except Exception as e:
            session_data['error'] = str(e)
        
        self.end_time = datetime.now()
        session_data['end_time'] = self.end_time.isoformat()
        session_data['duration_seconds'] = (self.end_time - self.start_time).total_seconds()
        
        return session_data


class PlaybookSuite:
    """Collection of different attacker playbooks"""
    
    def __init__(self, output_dir='playbook_results'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.playbooks = []
    
    def add_playbook(self, playbook):
        self.playbooks.append(playbook)
    
    @staticmethod
    def reconnaissance_playbook():
        """Playbook 1: Basic reconnaissance and version detection"""
        pb = AttackerPlaybook('Reconnaissance')
        pb.add_command('whoami', delay=1)
        pb.add_command('id', delay=1)
        pb.add_command('uname -a', delay=1)
        pb.add_command('cat /etc/issue', delay=1)
        pb.add_command('ps aux', delay=1)
        return pb
    
    @staticmethod
    def credential_search_playbook():
        """Playbook 2: Searching for credentials and secrets"""
        pb = AttackerPlaybook('Credential Search')
        pb.add_command('grep -r "password" /home', delay=1.5)
        pb.add_command('grep -r "key" ~/.ssh/', delay=1)
        pb.add_command('cat ~/.ssh/id_rsa', delay=1)
        pb.add_command('ls -la ~/.*', delay=1)
        pb.add_command('find /opt -name "*.conf" -o -name "*.key"', delay=2)
        pb.add_command('env | grep -i "pass\|key\|secret"', delay=1)
        return pb
    
    @staticmethod
    def privilege_escalation_playbook():
        """Playbook 3: Attempting privilege escalation"""
        pb = AttackerPlaybook('Privilege Escalation')
        pb.add_command('sudo -l', delay=1)
        pb.add_command('sudo su', delay=2)
        pb.add_command('id', delay=1)
        pb.add_command('cat /etc/sudoers', delay=1)
        pb.add_command('find / -perm -4000 2>/dev/null', delay=3)  # SUID binaries
        pb.add_command('apt list --upgradable 2>/dev/null', delay=1)
        return pb
    
    @staticmethod
    def data_staging_playbook():
        """Playbook 4: Preparing data for exfiltration"""
        pb = AttackerPlaybook('Data Staging')
        pb.add_command('find /var/www -type f -name "*.php" -o -name "*.js"', delay=2)
        pb.add_command('tar czf /tmp/backup.tar.gz /var/www/html', delay=3)
        pb.add_command('ls -lh /tmp/', delay=1)
        pb.add_command('du -sh /var/www', delay=1)
        pb.add_command('rsync -avz /var/www/ /tmp/staging/', delay=3)
        return pb
    
    @staticmethod
    def honeypot_fingerprinting_playbook():
        """Playbook 5: Attempting to detect honeypot"""
        pb = AttackerPlaybook('Honeypot Fingerprinting')
        pb.add_command('ls -la /.dockerenv', delay=0.5)  # Docker detection
        pb.add_command('cat /proc/cpuinfo | head -5', delay=1)
        pb.add_command('ifconfig -a 2>/dev/null || ip addr', delay=1)
        pb.add_command('arp -a', delay=1)
        pb.add_command('netstat -tulpn 2>/dev/null | head -20', delay=2)
        pb.add_command('ss -tulpn 2>/dev/null | head -20', delay=1)
        pb.add_command('cat /etc/mtab', delay=1)
        return pb
    
    @staticmethod
    def configuration_discovery_playbook():
        """Playbook 6: Finding and reading configuration files"""
        pb = AttackerPlaybook('Configuration Discovery')
        pb.add_command('cat /etc/nginx/nginx.conf', delay=1)
        pb.add_command('cat /etc/postgresql/postgresql.conf 2>/dev/null', delay=1)
        pb.add_command('cat /etc/mysql/my.cnf 2>/dev/null', delay=1)
        pb.add_command('find /etc -name "*.conf" | head -20', delay=2)
        pb.add_command('grep -r "internal\|secret\|api_key" /etc', delay=2)
        return pb
    
    @staticmethod
    def persistence_mechanisms_playbook():
        """Playbook 7: Installing persistence mechanisms"""
        pb = AttackerPlaybook('Persistence Mechanisms')
        pb.add_command('cat ~/.bashrc', delay=1)
        pb.add_command('echo "alias ls=\'ls -la\'" >> ~/.bashrc', delay=1)
        pb.add_command('crontab -l', delay=1)
        pb.add_command('(crontab -l; echo "* * * * * /tmp/beacon.sh") | crontab -', delay=1)
        pb.add_command('ls -la /etc/init.d/', delay=1)
        pb.add_command('cat /etc/rc.local', delay=1)
        return pb
    
    @staticmethod
    def lateral_movement_playbook():
        """Playbook 8: Attempting to move laterally"""
        pb = AttackerPlaybook('Lateral Movement')
        pb.add_command('cat /etc/hosts', delay=1)
        pb.add_command('nslookup db.internal 2>/dev/null', delay=2)
        pb.add_command('ping -c 3 10.0.1.50', delay=2)
        pb.add_command('ssh-keyscan -t rsa db.internal 2>/dev/null', delay=2)
        pb.add_command('nmap -sV 10.0.1.0/24 2>/dev/null', delay=5)
        return pb
    
    def generate_all_playbooks(self):
        """Create all playbook instances"""
        self.add_playbook(self.reconnaissance_playbook())
        self.add_playbook(self.credential_search_playbook())
        self.add_playbook(self.privilege_escalation_playbook())
        self.add_playbook(self.data_staging_playbook())
        self.add_playbook(self.honeypot_fingerprinting_playbook())
        self.add_playbook(self.configuration_discovery_playbook())
        self.add_playbook(self.persistence_mechanisms_playbook())
        self.add_playbook(self.lateral_movement_playbook())
    
    def execute_all(self, delay_between_playbooks=2):
        """Execute all playbooks and collect results"""
        all_results = []
        
        print("🎯 Executing attacker playbooks...")
        
        for i, playbook in enumerate(self.playbooks, 1):
            print(f"\n[{i}/{len(self.playbooks)}] Executing: {playbook.name}")
            
            try:
                result = playbook.execute()
                all_results.append(result)
                print(f"  ✓ {len(playbook.commands)} commands executed")
            except Exception as e:
                print(f"  ✗ Error: {e}")
                all_results.append({
                    'playbook': playbook.name,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
            
            time.sleep(delay_between_playbooks)
        
        # Save results
        results_file = self.output_dir / 'all_playbook_results.json'
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        print(f"\n✓ All playbooks executed. Results saved to {results_file}")
        
        return all_results

if __name__ == '__main__':
    suite = PlaybookSuite()
    suite.generate_all_playbooks()
    results = suite.execute_all()
    
    print("\n📊 Playbook Catalogue:")
    for pb in suite.playbooks:
        print(f"  - {pb.name}: {len(pb.commands)} commands")
