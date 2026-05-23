#!/usr/bin/env python3
"""
LLM-Based Decoy Artefact Generator
Generates believable fake files using Claude API for consistency
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import random

# For this version, we'll use template-based generation
# In production, you'd use: from anthropic import Anthropic

class DecoyArtifactGenerator:
    def __init__(self, output_dir='honeypot_decoys'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.artifact_inventory = []
        
        # Consistent usernames, hostnames for internal consistency
        self.system_config = {
            'hostname': 'web-prod-02',
            'domain': 'company.internal',
            'users': ['alice', 'bob', 'deployment', 'sysadmin'],
            'company': 'TechCorp Inc',
            'software_versions': {
                'nginx': '1.19.6',
                'postgres': '12.4',
                'python': '3.8.5',
                'openssh': '7.4p1',
            }
        }
    
    def generate_shell_history(self):
        """Generate a realistic .bash_history file"""
        history_commands = [
            "sudo systemctl restart nginx",
            "cd /var/www/html",
            "ls -la | grep config",
            "ps aux | grep postgres",
            "tail -f /var/log/nginx/access.log",
            "curl -I https://api.company.internal/health",
            "grep -r 'password' /etc/",
            "find . -name '*.backup' -o -name '*.old'",
            "cat /etc/shadow 2>/dev/null",
            "ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa",
            "for i in {1..255}; do ping -c 1 192.168.1.$i & done",
            "nmap -sV localhost",
            "whoami",
            "id",
            "sudo -l",
        ]
        
        history = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i, cmd in enumerate(history_commands):
            timestamp = base_time + timedelta(hours=i*2)
            history.append(cmd)
        
        content = "\n".join(history)
        
        file_path = self.output_dir / '.bash_history'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': '.bash_history',
            'category': 'shell_history',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'alice',
            'purpose': 'Show previous commands and exploration patterns'
        })
        
        return content
    
    def generate_nginx_config(self):
        """Generate a realistic nginx.conf snippet"""
        content = f"""# nginx configuration on {self.system_config['hostname']}
# Last modified: {(datetime.now() - timedelta(days=5)).isoformat()}

upstream backend {{
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
}}

server {{
    listen 80;
    server_name {self.system_config['domain']};
    
    location / {{
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }}
    
    location /admin {{
        auth_basic "Restricted";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8082;
    }}
    
    # Note: SSL certificates in /etc/ssl/certs/company_cert.pem
}}
"""
        file_path = self.output_dir / 'nginx.conf.snippet'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': 'nginx.conf.snippet',
            'category': 'configuration',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'sysadmin',
            'purpose': 'Show web server configuration and internal backend IPs'
        })
        
        return content
    
    def generate_fake_credentials_file(self):
        """Generate a file with deliberately enticing (but fake) credentials"""
        # These are fake - never use real credentials!
        credentials = {
            'prod_db': {
                'host': 'db.internal',
                'user': 'webapp_user',
                'password': 'Db@Pass2024_temp',  # Obviously fake
                'database': 'production'
            },
            'admin_panel': {
                'url': 'https://admin.company.internal',
                'username': 'admin',
                'password': 'AdminPass123!',  # Obviously fake
                'notes': 'Remember to change after deployment'
            },
            'api_key': 'sk-proj-0000000000000000000000000000'  # Fake format
        }
        
        content = json.dumps(credentials, indent=2)
        file_path = self.output_dir / '.env.example'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': '.env.example',
            'category': 'credentials',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'deployment',
            'purpose': 'Tempting fake credentials to measure attacker interest'
        })
        
        return content
    
    def generate_postgresql_logs(self):
        """Generate realistic PostgreSQL log entries"""
        log_entries = []
        base_time = datetime.now() - timedelta(hours=24)
        
        queries = [
            "SELECT * FROM users WHERE role='admin'",
            "CREATE USER backdoor WITH PASSWORD 'secret'",
            "ALTER USER webapp_user WITH SUPERUSER",
            "SELECT version()",
            "\\dt",  # list tables
        ]
        
        for i, query in enumerate(queries):
            timestamp = base_time + timedelta(minutes=i*30)
            log_entries.append(
                f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [12345] "
                f"user=postgres,db=postgres LOG: statement: {query}"
            )
        
        content = "\n".join(log_entries)
        file_path = self.output_dir / 'postgresql.log'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': 'postgresql.log',
            'category': 'logs',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'sysadmin',
            'purpose': 'Show database activity and potential privilege escalation attempts'
        })
        
        return content
    
    def generate_ssh_known_hosts(self):
        """Generate SSH known_hosts file showing internal network"""
        content = """# Known hosts
db.internal ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC1234567890...
cache.internal ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC0987654321...
backup.internal ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQCabcdefghij...
10.0.1.50 ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC5555555555...
"""
        file_path = self.output_dir / '.ssh_known_hosts'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': '.ssh_known_hosts',
            'category': 'ssh_keys',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'alice',
            'purpose': 'Reveal internal network topology and IP addresses'
        })
        
        return content
    
    def generate_cron_jobs(self):
        """Generate crontab entries showing scheduled tasks"""
        content = """# /etc/crontab: crontab entries for automated tasks
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# Backup jobs
0 2 * * * root /usr/local/bin/backup_db.sh >> /var/log/backup.log 2>&1
30 */4 * * * sysadmin /usr/bin/dump_tables.sh

# Maintenance
0 0 * * 0 root /usr/local/bin/cleanup.sh
*/15 * * * * deployment /opt/app/healthcheck.sh

# Hidden job (suspicious)
0 3 * * * root /tmp/.update.sh 2>/dev/null

# Reboot actions
@reboot root /opt/startup.sh
"""
        file_path = self.output_dir / 'crontab'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': 'crontab',
            'category': 'system_config',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'sysadmin',
            'purpose': 'Show scheduled tasks and potential persistence mechanisms'
        })
        
        return content
    
    def generate_firewall_rules(self):
        """Generate iptables/firewall rules"""
        content = """# Firewall rules (iptables format)
# Allow internal traffic
-A INPUT -s 10.0.0.0/8 -j ACCEPT
-A INPUT -s 192.168.0.0/16 -j ACCEPT

# SSH from specific IPs
-A INPUT -p tcp --dport 22 -s 203.0.113.5 -j ACCEPT
-A INPUT -p tcp --dport 22 -j DROP

# HTTP/HTTPS
-A INPUT -p tcp --dport 80 -j ACCEPT
-A INPUT -p tcp --dport 443 -j ACCEPT

# DNS
-A INPUT -p udp --dport 53 -j ACCEPT

# Database (internal only)
-A INPUT -p tcp --dport 5432 -s 10.0.1.0/24 -j ACCEPT

# Forward rules
-A FORWARD -o eth1 -j ACCEPT
-A FORWARD -i eth1 -j ACCEPT
"""
        file_path = self.output_dir / 'firewall_rules.txt'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': 'firewall_rules.txt',
            'category': 'network_config',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'sysadmin',
            'purpose': 'Reveal firewall policies and allow attackers to plan network movement'
        })
        
        return content
    
    def generate_admin_notes(self):
        """Generate seemingly important admin notes"""
        content = """# TODO List - Web Prod Environment
## Security
- [ ] Update OpenSSH from 7.4 to 8.2 (CRITICAL CVE-2020-14145)
- [ ] Apply PostgreSQL security patches
- [ ] Rotate database credentials
- [ ] Review user permissions - deployment user has too much access
- [ ] Disable root login via SSH

## Infrastructure
- [ ] Add load balancer for db failover
- [ ] Increase backup frequency to hourly
- [ ] Test disaster recovery procedures
- [ ] Monitor disk space on backup server

## Credentials to update:
- Postgres webapp_user@db.internal
- Admin panel API key
- AWS credentials in /root/.aws/

## Known Issues
- Memory leak in service on port 8082 (needs restart weekly)
- Slow queries on users table after 1M records
- Cache invalidation race condition

## Scheduled Maintenance
- 2024-01-15: Full system patching window (02:00-04:00 UTC)
"""
        file_path = self.output_dir / 'ADMIN_NOTES.txt'
        with open(file_path, 'w') as f:
            f.write(content)
        
        self.artifact_inventory.append({
            'name': 'ADMIN_NOTES.txt',
            'category': 'documentation',
            'path': str(file_path),
            'llm_generated': False,
            'user': 'sysadmin',
            'purpose': 'Create sense of urgency and reveal security gaps'
        })
        
        return content
    
    def generate_inventory(self):
        """Create and save the artifact inventory"""
        inventory_file = self.output_dir / 'artifact_inventory.json'
        with open(inventory_file, 'w') as f:
            json.dump(self.artifact_inventory, f, indent=2)
        
        return self.artifact_inventory
    
    def generate_all(self):
        """Generate all decoy artifacts"""
        print("🎭 Generating decoy artefacts...")
        
        self.generate_shell_history()
        print("✓ Shell history")
        
        self.generate_nginx_config()
        print("✓ Nginx config")
        
        self.generate_fake_credentials_file()
        print("✓ Credentials file")
        
        self.generate_postgresql_logs()
        print("✓ PostgreSQL logs")
        
        self.generate_ssh_known_hosts()
        print("✓ SSH known hosts")
        
        self.generate_cron_jobs()
        print("✓ Cron jobs")
        
        self.generate_firewall_rules()
        print("✓ Firewall rules")
        
        self.generate_admin_notes()
        print("✓ Admin notes")
        
        inventory = self.generate_inventory()
        print(f"\n✓ Total artifacts generated: {len(inventory)}")
        print(f"📁 Location: {self.output_dir.absolute()}")
        
        return inventory

if __name__ == '__main__':
    generator = DecoyArtifactGenerator()
    inventory = generator.generate_all()
    
    print("\n📋 Artifact Inventory:")
    for artifact in inventory:
        print(f"  - {artifact['name']} ({artifact['category']})")
