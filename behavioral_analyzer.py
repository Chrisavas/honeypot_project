#!/usr/bin/env python3
"""
Behavioural Analysis Engine
Analyzes honeypot logs to extract intent and patterns
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import statistics

class BehaviouralAnalyzer:
    def __init__(self, log_dir='honeypot_logs', playbook_dir='playbook_results'):
        self.log_dir = Path(log_dir)
        self.playbook_dir = Path(playbook_dir)
        self.sessions = []
        self.playbook_results = []
    
    def load_honeypot_logs(self):
        """Load all honeypot session logs"""
        master_log = self.log_dir / 'master_log.jsonl'
        
        if not master_log.exists():
            print("⚠️  No master log found")
            return []
        
        with open(master_log, 'r') as f:
            for line in f:
                try:
                    session = json.loads(line)
                    self.sessions.append(session)
                except:
                    pass
        
        print(f"📖 Loaded {len(self.sessions)} sessions")
        return self.sessions
    
    def load_playbook_results(self):
        """Load playbook execution results"""
        results_file = self.playbook_dir / 'all_playbook_results.json'
        
        if results_file.exists():
            with open(results_file, 'r') as f:
                self.playbook_results = json.load(f)
        
        print(f"📋 Loaded {len(self.playbook_results)} playbook results")
        return self.playbook_results
    
    def compute_dwell_time(self, session):
        """Compute how long the attacker spent in a session"""
        if not session.get('events') or len(session['events']) < 2:
            return 0
        
        first_event = session['events'][0]
        last_event = session['events'][-1]
        
        try:
            start = datetime.fromisoformat(first_event['time'])
            end = datetime.fromisoformat(last_event['time'])
            return (end - start).total_seconds()
        except:
            return 0
    
    def compute_command_diversity(self, playbook_result):
        """Measure the variety of commands issued"""
        if not playbook_result.get('commands_executed'):
            return 0
        
        commands = [cmd['command'] for cmd in playbook_result['commands_executed']]
        unique_commands = len(set(commands))
        total_commands = len(commands)
        
        # Diversity score: unique / total
        if total_commands == 0:
            return 0
        return unique_commands / total_commands
    
    def classify_intent(self, playbook_result):
        """Classify likely attacker intent based on commands"""
        if 'error' in playbook_result:
            return 'connection_failed'
        
        playbook_name = playbook_result.get('playbook', 'Unknown')
        
        # Map playbook names to intents
        intent_map = {
            'Reconnaissance': 'reconnaissance',
            'Credential Search': 'credential_harvesting',
            'Privilege Escalation': 'privilege_escalation',
            'Data Staging': 'data_exfiltration',
            'Honeypot Fingerprinting': 'honeypot_detection',
            'Configuration Discovery': 'environment_mapping',
            'Persistence Mechanisms': 'persistence',
            'Lateral Movement': 'lateral_movement',
        }
        
        return intent_map.get(playbook_name, 'unknown')
    
    def compute_depth_score(self, playbook_result):
        """Score how deeply the attacker engaged with the environment"""
        score = 0
        
        if not playbook_result.get('commands_executed'):
            return 0
        
        commands = [cmd['command'] for cmd in playbook_result['commands_executed']]
        
        # +1 for each command
        score += len(commands)
        
        # +5 if any credential-related commands
        if any('pass' in cmd.lower() or 'key' in cmd.lower() for cmd in commands):
            score += 5
        
        # +3 if trying privilege escalation
        if any('sudo' in cmd.lower() or 'su' in cmd.lower() for cmd in commands):
            score += 3
        
        # +3 if trying to access restricted files
        if any('/etc/shadow' in cmd or '/root' in cmd for cmd in commands):
            score += 3
        
        # +2 if exploring configuration
        if any('.conf' in cmd or 'config' in cmd.lower() for cmd in commands):
            score += 2
        
        # Duration bonus
        duration = playbook_result.get('duration_seconds', 0)
        score += min(duration / 10, 5)  # Max 5 points for duration
        
        return score
    
    def generate_session_summary(self, playbook_result):
        """Generate a human-readable summary of a session"""
        intent = self.classify_intent(playbook_result)
        depth = self.compute_depth_score(playbook_result)
        diversity = self.compute_command_diversity(playbook_result)
        duration = playbook_result.get('duration_seconds', 0)
        
        commands_issued = len(playbook_result.get('commands_executed', []))
        
        summary = {
            'playbook': playbook_result.get('playbook', 'Unknown'),
            'intent': intent,
            'depth_score': round(depth, 2),
            'command_diversity': round(diversity, 2),
            'duration_seconds': round(duration, 2),
            'commands_issued': commands_issued,
            'narrative': self._generate_narrative(playbook_result, intent, depth)
        }
        
        return summary
    
    def _generate_narrative(self, result, intent, depth):
        """Generate a narrative description of the session"""
        commands = result.get('commands_executed', [])
        
        if not commands:
            return "Attacker connected but issued no commands."
        
        narratives = {
            'reconnaissance': "The attacker performed basic system enumeration, gathering information about the OS, running processes, and system configuration. This suggests initial network reconnaissance activity.",
            
            'credential_harvesting': "The attacker actively searched for credentials and sensitive data, including SSH keys and configuration files. This indicates intent to gain higher privileges or access other systems.",
            
            'privilege_escalation': "The attacker attempted to escalate privileges using sudo and other escalation vectors. This is a critical attack stage indicating persistence intent.",
            
            'data_exfiltration': "The attacker staged data for exfiltration, creating archives and preparing stolen information. This suggests the attack has progressed beyond reconnaissance.",
            
            'honeypot_detection': "The attacker performed specific checks to detect honeypot/sandbox environments, including Docker, VM, and environment analysis. This indicates a sophisticated attacker.",
            
            'environment_mapping': "The attacker mapped the network environment by reading configuration files and discovering other systems. Preparation for lateral movement.",
            
            'persistence': "The attacker attempted to install persistence mechanisms for maintaining future access.",
            
            'lateral_movement': "The attacker probed for network connectivity to other internal systems, preparing for lateral movement.",
        }
        
        base_narrative = narratives.get(intent, "Unknown attack pattern detected.")
        
        depth_descriptor = "shallow" if depth < 10 else "moderate" if depth < 20 else "deep"
        
        return f"{base_narrative} Engagement depth: {depth_descriptor}."
    
    def analyze_all_sessions(self):
        """Run complete behavioral analysis"""
        print("\n🔍 Analyzing session behaviour...")
        
        # Load data
        self.load_honeypot_logs()
        self.load_playbook_results()
        
        # Compute metrics
        summaries = []
        for result in self.playbook_results:
            summary = self.generate_session_summary(result)
            summaries.append(summary)
        
        # Group by intent
        by_intent = defaultdict(list)
        for summary in summaries:
            by_intent[summary['intent']].append(summary)
        
        # Save results
        analysis = {
            'total_sessions': len(summaries),
            'session_summaries': summaries,
            'intent_distribution': {
                intent: len(sessions) 
                for intent, sessions in by_intent.items()
            },
            'average_depth_score': round(statistics.mean([s['depth_score'] for s in summaries]), 2) if summaries else 0,
            'average_command_diversity': round(statistics.mean([s['command_diversity'] for s in summaries]), 2) if summaries else 0,
            'average_session_duration': round(statistics.mean([s['duration_seconds'] for s in summaries]), 2) if summaries else 0,
        }
        
        # Save analysis
        analysis_file = self.log_dir / 'behavioural_analysis.json'
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"✓ Analysis saved to {analysis_file}")
        
        return analysis
    
    def print_summary(self, analysis):
        """Print a formatted summary"""
        print("\n" + "="*60)
        print("📊 BEHAVIOURAL ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"\nTotal Sessions: {analysis['total_sessions']}")
        print(f"Average Engagement Depth: {analysis['average_depth_score']}/50")
        print(f"Average Command Diversity: {analysis['average_command_diversity']:.2%}")
        print(f"Average Session Duration: {analysis['average_session_duration']:.1f}s")
        
        print("\nIntent Distribution:")
        for intent, count in sorted(analysis['intent_distribution'].items()):
            print(f"  - {intent}: {count} sessions")
        
        print("\nTop 3 Sessions by Engagement Depth:")
        summaries = sorted(analysis['session_summaries'], 
                          key=lambda s: s['depth_score'], 
                          reverse=True)[:3]
        
        for i, summary in enumerate(summaries, 1):
            print(f"\n  {i}. {summary['playbook']}")
            print(f"     Intent: {summary['intent']}")
            print(f"     Depth: {summary['depth_score']}/50")
            print(f"     Narrative: {summary['narrative']}")
        
        print("\n" + "="*60)

if __name__ == '__main__':
    analyzer = BehaviouralAnalyzer()
    analysis = analyzer.analyze_all_sessions()
    analyzer.print_summary(analysis)
