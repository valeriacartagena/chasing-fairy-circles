import pandas as pd
import numpy as np
from dataclasses import dataclass, field

# Implementation of Online planning with heuristic search and UCB exploration (Ch. 21 DMU book)

@dataclass
class POMDPAgent:
    environment: object  # FCEnvironment
    belief_init_val: float = 0.2 # Initial uniform belief value

    pDetectIfHydrogen: float = 0.75    # P(detect hydrogen | hydrogen present)
    pDetectIfNoHydrogen: float = 0.1   # P(detect hydrogen | no hydrogen)
    
    drill_threshold: float = 0.35
    ucb_coefficient: float = 1.0

    n_cells: int = field(init=False)
    belief: np.ndarray = field(init=False)
    total_reward: float = field(default=0.0, init=False)
    history: list = field(default_factory=list, init=False)

    # Initialize fields after dataclass creation
    def __post_init__(self):
        self.n_cells = self.environment.n_cells
        if hasattr(self.environment, 'df'):
            ndvi_values = self.environment.df['current_NDVI'].values
            normalized = (ndvi_values.max() - ndvi_values) / (ndvi_values.max() - ndvi_values.min())
            self.belief = np.clip(normalized * 0.4 + 0.1, 0.1, 0.5)
        else:
            self.belief = np.full(self.n_cells, self.belief_init_val)
        
        self.total_reward = 0.0
        self.history = []

    def update_belief(self, cell_id: int, observations: bool):
        observation = observations['signal']
        prior = self.belief[cell_id]

        if observation:
            likelihood_hydrogen = self.pDetectIfHydrogen
            likelihood_no_hydrogen = self.pDetectIfNoHydrogen
        else:  # No signal
            likelihood_hydrogen = 1 - self.pDetectIfHydrogen
            likelihood_no_hydrogen = 1 - self.pDetectIfNoHydrogen

        marginal = likelihood_hydrogen * prior + likelihood_no_hydrogen * (1 - prior)
        posterior = (likelihood_hydrogen * prior) / marginal if marginal > 0 else prior
        
        logit = np.log(self.belief[cell_id]/(1-self.belief[cell_id]))
        self.belief[cell_id] = np.clip(posterior, 0.001, 0.999)
    
    def random_policy(self):
        new_spot = [
            i for i in range(self.n_cells)
            if i not in self.environment.surveyed_cells and i not in self.environment.drilled_cells
        ]
        if not new_spot:
            return None, None
        
        cell = np.random.choice(new_spot)
        action = np.random.choice(['ignore', 'survey', 'drill'], p=[0.6, 0.3, 0.1])
        return cell, action
    
    def greedy_policy(self):
        # Only exclude drilled cells (can re-survey)
        new_spot = [
            i for i in range(self.n_cells)
            if i not in self.environment.drilled_cells
        ]
        if not new_spot:
            return None, None
        
        cell = max(new_spot, key=lambda i: self.belief[i])
        
        
        if self.belief[cell] >= self.drill_threshold:
            action = 'drill'
        elif cell not in self.environment.surveyed_cells:
            action = 'survey'  
        elif self.belief[cell] >= 0.4: 
            action = 'survey'
        else:
            action = 'drill' 
            
        return cell, action

    # Calculate entropy to use in UCB uncertainty value
    def _calc_entropy(self, belief: float) -> float:
        if belief <= 0 or belief >= 1:
            return 0
        return -belief * np.log2(belief) - (1 - belief) * np.log2(1 - belief)

    def ucb_policy(self, c=None):
        if c is None:
            c = self.ucb_coefficient
        
        available = [i for i in range(self.n_cells) 
                    if i not in self.environment.drilled_cells]
        
        if not available:
            return None, None
        
        scores = {}
        for i in available:
            exploitation = self.belief[i]
            uncertainty = self._calc_entropy(self.belief[i])
            
            survey_bonus = 0.2 if i not in self.environment.surveyed_cells else 0
            
            scores[i] = exploitation + c * uncertainty + survey_bonus
        
        cell = max(scores, key=scores.get)
        
        if self.belief[cell] >= self.drill_threshold:
            action = 'drill'
        else:
            action = 'survey'
        
        return cell, action
    
    # Run a single episode with specified policy
    def run_episode(self, policy, budget=1500):
        # Reset everything
        self.belief = np.full(self.n_cells, self.belief_init_val)
        self.total_reward = 0.0
        self.history = []   
        self.environment.surveyed_cells = set()
        self.environment.drilled_cells = set()
        spent = 0
        step = 0
        n_discoveries = 0

        while spent < budget:
        
            if policy == 'random':
                cell, action = self.random_policy()
            elif policy == 'greedy':
                cell, action = self.greedy_policy()
            elif policy == 'ucb':
                cell, action = self.ucb_policy()
            else:
                raise ValueError(f"Unknown policy: {policy}")

            if cell is None or action is None:
                break  # No more actions possible!
            
            current_reward = 0
            observation_data = {}
            is_discovery = False

            if action == 'ignore':
                observation_data = self.environment.ignore()
                current_reward = observation_data['reward']

            elif action == 'survey':
                observation_data = self.environment.survey(cell)
                self.update_belief(cell, observation_data)
                current_reward = observation_data['cost'] # Cost is the reward for the agent
                spent += -current_reward

            elif action == 'drill':
                observation_data = self.environment.drill(cell)
                current_reward = observation_data['reward']
                spent += -observation_data['cost'] # NOTE: If cost is negative, this increases 'spent'
                if observation_data['discovery']:
                    n_discoveries += 1
                    is_discovery = True

            else:
                raise ValueError(f"Unknown action: {action}")

            self.total_reward += current_reward
            self.history.append({
                'step': step,
                'cell': cell,
                'action': action,
                'reward': current_reward, 
                'belief': self.belief[cell],
                'observation': observation_data, 
                'total_reward': self.total_reward,
                'discovery': is_discovery
            })
            step += 1
        return self.total_reward, self.history
    
    def get_stats(self):
        if not self.history:
            return {}
        
        surveys = [h for h in self.history if h['action'] == 'survey']
        drills = [h for h in self.history if h['action'] == 'drill']
        discoveries = [h for h in drills if h['discovery']]

        return {
            'total_steps': len(self.history),
            'n_surveys': len(surveys),
            'n_drills': len(drills),
            'n_discoveries': len(discoveries),
            'total_reward': self.total_reward,
            'avg_belief_drill': np.mean([h['belief'] for h in drills]) if drills else 0,
            'discovery_rate': len(discoveries) / len(drills) if drills else 0,
            'total_spent': -sum([h['reward'] for h in self.history if h['reward'] < 0]),
            'reward_per_usd': self.total_reward / -sum([h['reward'] for h in self.history if h['reward'] < 0]) if sum([h['reward'] for h in self.history if h['reward'] < 0]) < 0 else 0
        }

def run_all_policies(environment, policies=['random', 'greedy', 'ignore'], n_trials=25, budget=5000):
    results = []

    for policy in policies:
        for trial in range(n_trials):
            agent = POMDPAgent(environment=environment)
            total_reward, history = agent.run_episode(policy=policy, budget=budget)
            stats = agent.get_stats()
            stats.update({
                'policy': policy,
                'trial': trial,
                'location': environment.loc_name
            })
            results.append(stats)
    
    return pd.DataFrame(results)
    