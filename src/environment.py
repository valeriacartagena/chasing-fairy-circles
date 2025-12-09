import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Set, List
from sklearn.cluster import KMeans

@dataclass
class FCEnvironment():
    df: pd.DataFrame
    loc_name: str

    # Initialization of fields
    n_cells: int = field(init=False)
    feature_cols: List[str] = field(init=False)
    true_hydrogen: Set[int] = field(init=False)
    
    # Mutable states
    surveyed_cells: Set[int] = field(default_factory=set)
    drilled_cells: Set[int] = field(default_factory=set)


    def __post_init__(self):
        self.df = (self.df[self.df['location'] == self.loc_name].copy().reset_index(drop=True))
        self.n_cells = len(self.df)
        self.feature_cols = [col for col in self.df.columns if col.startswith('pca')]
        self.true_hydrogen = self._hydrogen_simulation()
    
    def _hydrogen_simulation(self) -> Set[int]:
        # We will use clustering to simulate true hydrogen locations
        feature_cols = [col for col in self.df.columns if col.startswith('pca')]
        X = self.df[feature_cols].values

        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        # Assuming the hydrogen cluster has lowe mean NDVI values
        mean_ndvi_cluster_0 = self.df[labels == 0]['current_NDVI'].mean()
        mean_ndvi_cluster_1 = self.df[labels == 1]['current_NDVI'].mean()

        hydrogen_cluster = 0 if mean_ndvi_cluster_0 < mean_ndvi_cluster_1 else 1
        hydrogen_indices = set(self.df.index[labels == hydrogen_cluster])

        return hydrogen_indices

    # Possible actions: survey or drill
    def ignore(self):
        return{
            'discovery': None,
            'cost': 0,
            'reward': 0
        }

    def survey(self, cell_id: int): # Returns noisy observations
        if cell_id in self.surveyed_cells:
            raise ValueError(f"Cell {cell_id} has already been surveyed.")
        
        self.surveyed_cells.add(cell_id)

        # Noisy observations
        features = self.df.loc[cell_id, self.feature_cols].values
        noise = np.random.normal(0, 0.1, size=len(features))
        observed = features + noise

        # Binary noisy signal for hydrogen presence
        has_H2 = cell_id in self.true_hydrogen
        detection_prob = 0.8 if has_H2 else 0.2
        signal = np.random.random() < detection_prob
        
        return {'observed_features': observed, 'signal': signal, 'cost': -500}
    
    def drill(self, cell_id: int): # Returns success and reward
        if cell_id in self.drilled_cells:
            raise ValueError(f"Cell {cell_id} has already been drilled.")
        
        self.drilled_cells.add(cell_id)

        # Logic is that drilling yields high reward if hydrogen is present, but it is costly otherwise
        discovery_reward = 10000
        cost_drill_success = - 200
        cost_drill_failure = -400

        has_H2 = cell_id in self.true_hydrogen

        if has_H2:
            reward = discovery_reward + cost_drill_success
            drill_cost = cost_drill_success
        else:
            reward = cost_drill_failure
            drill_cost = cost_drill_failure

        return {'discovery': has_H2, 'cost': drill_cost , 'reward': reward}