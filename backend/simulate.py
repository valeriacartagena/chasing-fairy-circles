import pandas as pd
import numpy as np
import base64
import pickle
import sys
import os

from environment import FCEnvironment
from pomdp_agent import POMDPAgent
from sklearn.cluster import KMeans

def sanitize_for_json(obj):
    """Recursively convert numpy / set types to native Python for JSON serialization."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, set):
        return list(obj)
    return obj

def get_region_df(df: pd.DataFrame, region: str) -> pd.DataFrame:
    """Filter dataframe based on region, or combine if 'All Three'"""
    if region.lower() == 'all three':
        # Create a combined pseudo-region logic or just use the whole dataframe
        # Given the environment expects a single loc_name, we can bypass the environment's filter
        # by creating a copy of the dataframe where all locations are set to 'All Three'
        combined_df = df.copy()
        combined_df['original_location'] = combined_df['location']
        combined_df['location'] = 'All Three'
        return combined_df
    else:
        # Standard filter
        return df[df['location'].str.lower() == region.lower()].copy()

def run_simulation(df_full: pd.DataFrame, region: str, policy: str, budget: float, n_trials: int, exploration_constant: float):
    df_region = get_region_df(df_full, region)
    if len(df_region) == 0:
        raise ValueError(f"No data found for region: {region}")

    # Use 'All Three' as the loc_name if combining, otherwise the original region name
    loc_name = 'All Three' if region.lower() == 'all three' else df_region['location'].iloc[0]
    
    results = []
    
    for trial in range(n_trials):
        env = FCEnvironment(df_region, loc_name)
        agent = POMDPAgent(environment=env)
        
        # Override UCB constant if provided
        agent.ucb_coefficient = exploration_constant
        
        total_reward, history = agent.run_episode(policy=policy, budget=budget)
        stats = agent.get_stats()
        
        # We also want the belief history over time for the frontend chart.
        # history contains dicts with 'belief'. Since we only track belief[cell], 
        # reconstructing full belief history is tricky. 
        # But for MVP, the history block contains what we need.
        
        trial_result = {
            "stats": sanitize_for_json(stats),
            "actions_log": sanitize_for_json(history),
            "rewards": float(total_reward),
        }
        results.append(trial_result)
        
    return results

def step_simulation(df_full: pd.DataFrame, region: str, policy: str, budget: float, exploration_constant: float, state_token: str | None,
                    cost_survey: float = 50.0, cost_drill_success: float = 200.0, cost_drill_fail: float = 400.0):
    # If starting fresh
    if not state_token:
        df_region = get_region_df(df_full, region)
        if len(df_region) == 0:
             raise ValueError(f"No data found for region: {region}")
             
        loc_name = 'All Three' if region.lower() == 'all three' else df_region['location'].iloc[0]
        env = FCEnvironment(df_region, loc_name)
        agent = POMDPAgent(environment=env)
        agent.ucb_coefficient = exploration_constant
        
        state = {
            'agent': agent,
            'spent': 0.0,
            'step': 0,
            'n_discoveries': 0,
            'is_done': False,
            'budget': budget, # Store initial budget config
            'budget_remaining': budget
        }
    else:
        # Deserialize state
        try:
            state_bytes = base64.b64decode(state_token)
            state = pickle.loads(state_bytes)
        except Exception as e:
            raise ValueError(f"Invalid state_token: {e}")
            
    agent = state['agent']
    env = agent.environment
    spent = state['spent']
    step_count = state['step']
    n_discoveries = state['n_discoveries']
    
    if state['is_done'] or spent >= budget:
        return {
            "is_done": True, 
            "message": "Budget exhausted or simulation complete.",
            "budget_remaining": max(0, budget - spent),
            "state_token": serialize_state(state)
        }
        
    # Execute exactly NEXT step
    if policy == 'random':
        cell, action = agent.random_policy()
    elif policy == 'greedy':
        cell, action = agent.greedy_policy()
    elif policy == 'ucb':
        # Apply current coefficient
        agent.ucb_coefficient = exploration_constant
        cell, action = agent.ucb_policy()
    else:
        raise ValueError(f"Unknown policy: {policy}")
        
    if cell is None or action is None:
        state['is_done'] = True
        return {
             "is_done": True,
             "message": "No actions left",
             "budget_remaining": max(0, budget - spent),
             "state_token": serialize_state(state)
         }
        
    current_reward = 0
    observation_data = {}
    is_discovery = False
    
    # Use frontend-provided costs for budget tracking (override defaults)
    actual_survey_cost_for_budget = cost_survey
    actual_drill_success_cost = cost_drill_success
    actual_drill_fail_cost = cost_drill_fail
    
    budget_cost = 0.0
    
    if action == 'ignore':
        observation_data = env.ignore()
        current_reward = observation_data['reward']
        budget_cost = 0.0 # Ignore is 0 cost
        
    elif action == 'survey':
        observation_data = env.survey(cell)
        agent.update_belief(cell, observation_data)
        current_reward = observation_data['cost'] # Keep reward logic unchanged
        budget_cost = actual_survey_cost_for_budget
        
    elif action == 'drill':
         observation_data = env.drill(cell)
         current_reward = observation_data['reward']
         if observation_data['discovery']:
             budget_cost = actual_drill_success_cost
             n_discoveries += 1
             is_discovery = True
         else:
             budget_cost = actual_drill_fail_cost
             
    agent.total_reward += current_reward
    spent += budget_cost
    
    # We must format observation_data to be JSON serializable
    # numpy arrays -> lists, bool_ -> bool, etc
    clean_obs = {}
    for k, v in observation_data.items():
         if isinstance(v, np.ndarray):
              clean_obs[k] = v.tolist()
         elif isinstance(v, np.bool_):
              clean_obs[k] = bool(v)
         else:
              clean_obs[k] = v
              
    step_result_entry = {
        'step': step_count,
        'cell': int(cell),
        'action': action,
        'reward': float(current_reward),
        'budget_cost_applied': float(budget_cost),
        'belief': float(agent.belief[cell]),
        'observation': clean_obs,
        'total_reward': float(agent.total_reward),
        'discovery': is_discovery
    }
    agent.history.append(step_result_entry)
    
    step_count += 1
    
    # Update state
    state['agent'] = agent
    state['spent'] = spent
    state['step'] = step_count
    state['n_discoveries'] = n_discoveries
    state['budget_remaining'] = float(max(0, budget - spent))
    
    # Check if budget exhausted this turn
    if spent >= budget:
        state['is_done'] = True
        
    import copy
    
    # Package response (Frontend needs array of all beliefs)
    response = {
         "action": action,
         "cell_idx": int(cell),
         "observation": clean_obs,
         "new_belief": float(agent.belief[cell]),
         "all_beliefs": agent.belief.tolist(), # Entire array for heatmap
         "reward": float(current_reward),
         "budget_remaining": state['budget_remaining'],
         "is_discovery": is_discovery,
         "is_done": state['is_done'],
         "state_token": serialize_state(state),
         "step_log": step_result_entry
    }
    
    return response


def serialize_state(state: dict) -> str:
    """Pickle and base64 encode the state dictionary."""
    state_bytes = pickle.dumps(state)
    return base64.b64encode(state_bytes).decode('utf-8')
