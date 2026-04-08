#!/usr/bin/env python

\"\"\"Baseline inference script for OpenEnv hackathon.\"\"\"
import json
import requests
import os
from typing import Dict, Any

HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('OPENAI_API_KEY')

BASE_URL = 'http://localhost:7860'

def reset_env() -> Dict[str, Any]:
    """Reset environment."""
    resp = requests.post(f'{BASE_URL}/reset')
    resp.raise_for_status()
    return resp.json()

def step_env(action: Dict[str, Any]) -> Dict[str, Any]:
    """Take step in environment."""
    resp = requests.post(f'{BASE_URL}/step', json=action)
    resp.raise_for_status()
    return resp.json()

def run_baseline(num_episodes: int = 10):
    """Run baseline evaluation."""
    results = []
    
    for episode in range(num_episodes):
        obs = reset_env()
        print(f'Episode {episode+1}: {obs["observation"]}')
        
        # Simple policy: always 'academic' for email task
        action = {'action': 'academic'}
        step_result = step_env(action)
        
        results.append({
            'episode': episode + 1,
            'reward': step_result['reward'],
            'done': step_result['done']
        })
        print(f'Reward: {step_result["reward"]}')
    
    avg_reward = sum(r['reward'] for r in results) / len(results)
    print(f'Average reward: {avg_reward:.3f}')
    return results

if __name__ == '__main__':
    run_baseline()

