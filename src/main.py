import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

from environment import FCEnvironment
from pomdp_agent import POMDPAgent, run_all_policies

# Set random seed for reproducibility
np.random.seed(42)

OUTPUT_DIR = './src'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Experiment parameters
POLICIES = ['random', 'greedy', 'ucb']
N_TRIALS = 20
BUDGET = 5000


# Data loading
df = pd.read_csv(f'gee_features_pca.csv')
print(f"  Loaded {len(df)} cells")
print(f"  Locations: {df['location'].unique()}")
print(f"  Features: {[c for c in df.columns if c.startswith('pc')]}")


# Experiments
all_results = []

for location in df['location'].unique():
    print(f"LOCATION: {location.upper()}")
    
    # Create environment
    env = FCEnvironment(df, location)
    print(f"  Environment: {env.n_cells} cells, {len(env.true_hydrogen)} with hydrogen")
    
    # Run policy comparison
    results = run_all_policies(
        environment=env,
        policies=POLICIES,
        n_trials=N_TRIALS,
        budget=BUDGET
    )
    
    all_results.append(results)
    
    # Quick summary
    summary = results.groupby('policy').agg({
        'total_reward': 'mean',
        'n_discoveries': 'mean',
        'discovery_rate': 'mean'
    }).round(2)
    print(f"\n  Summary for {location}:")
    print(summary)

# Combine all results
results_df = pd.concat(all_results, ignore_index=True)

# Save raw results
results_path = f'{OUTPUT_DIR}/experiment_results.csv'
results_df.to_csv(results_path, index=False)


# Overall statistics
overall_stats = results_df.groupby('policy').agg({
    'total_reward': ['mean', 'std', 'min', 'max'],
    'n_discoveries': ['mean', 'std'],
    'n_surveys': ['mean', 'std'],
    'n_drills': ['mean', 'std'],
    'discovery_rate': ['mean', 'std']
}).round(3)

print("\nOverall Statistics:")
print(overall_stats)

# Per-location statistics
location_stats = results_df.groupby(['location', 'policy']).agg({
    'total_reward': 'mean',
    'n_discoveries': 'mean',
    'discovery_rate': 'mean'
}).round(2)

print("\nPer-Location Statistics:")
print(location_stats)

# Save statistics
overall_stats.to_csv(f'{OUTPUT_DIR}/statistics_overall.csv')
location_stats.to_csv(f'{OUTPUT_DIR}/statistics_by_location.csv')

# Statistical significance tests

from scipy import stats

significance_results = []

for location in df['location'].unique():
    loc_data = results_df[results_df['location'] == location]
    
    # Test greedy vs random
    greedy_rewards = loc_data[loc_data['policy'] == 'greedy']['total_reward']
    random_rewards = loc_data[loc_data['policy'] == 'random']['total_reward']
    
    if len(greedy_rewards) > 0 and len(random_rewards) > 0:
        t_stat, p_value = stats.ttest_ind(greedy_rewards, random_rewards)
        
        
        pooled_std = np.sqrt((greedy_rewards.std()**2 + random_rewards.std()**2) / 2)
        cohens_d = (greedy_rewards.mean() - random_rewards.mean()) / pooled_std if pooled_std > 0 else 0
        
        significance_results.append({
            'location': location,
            'comparison': 'greedy vs random',
            'greedy_mean': greedy_rewards.mean(),
            'random_mean': random_rewards.mean(),
            'difference': greedy_rewards.mean() - random_rewards.mean(),
            't_statistic': t_stat,
            'p_value': p_value,
            'cohens_d': cohens_d,
            'significant_p005': p_value < 0.05
        })
        
        print(f"\n{location}:")
        print(f"  Greedy: {greedy_rewards.mean():.1f} ± {greedy_rewards.std():.1f}")
        print(f"  Random: {random_rewards.mean():.1f} ± {random_rewards.std():.1f}")
        print(f"  Difference: {greedy_rewards.mean() - random_rewards.mean():.1f}")
        print(f"  p-value: {p_value:.4f} {'**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'}")
        print(f"  Cohen's d: {cohens_d:.3f}")

sig_df = pd.DataFrame(significance_results)
sig_df.to_csv(f'{OUTPUT_DIR}/statistical_tests.csv', index=False)

# Visualizations

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300

# Figure 1: Policy Comparison - Overall Performance
fig1, axes = plt.subplots(4, 1, figsize=(10, 14))

colors = {'random': 'gray', 'greedy': 'blue', 'ucb': 'green'}

# Plot 1: Total reward distribution
for policy in POLICIES:
    data = results_df[results_df['policy'] == policy]['total_reward']
    axes[0].hist(data, bins=15, alpha=0.6, label=policy, color=colors[policy])
axes[0].set_xlabel('Total Reward', fontsize=11)
axes[0].set_ylabel('Frequency', fontsize=11)
axes[0].set_title('Total Reward Distribution by Policy', fontsize=12, fontweight='bold')
axes[0].legend()
axes[0].grid(alpha=0.3)

# Plot 2: Average discoveries
discovery_means = results_df.groupby('policy')['n_discoveries'].agg(['mean', 'std'])
x = np.arange(len(POLICIES))
axes[1].bar(x, discovery_means['mean'], yerr=discovery_means['std'],
            capsize=5, alpha=0.7, color=[colors[p] for p in POLICIES])
axes[1].set_xticks(x)
axes[1].set_xticklabels(POLICIES)
axes[1].set_ylabel('Number of Discoveries', fontsize=11)
axes[1].set_title('Average Discoveries per Policy', fontsize=12, fontweight='bold')
axes[1].grid(alpha=0.3, axis='y')

# Plot 3: Discovery rate
rate_means = results_df.groupby('policy')['discovery_rate'].agg(['mean', 'std'])
axes[2].bar(x, rate_means['mean'], yerr=rate_means['std'],
            capsize=5, alpha=0.7, color=[colors[p] for p in POLICIES])
axes[2].set_xticks(x)
axes[2].set_xticklabels(POLICIES)
axes[2].set_ylabel('Discovery Rate', fontsize=11)
axes[2].set_title('Success Rate (Discoveries / Drills)', fontsize=12, fontweight='bold')
axes[2].set_ylim([0, 1])
axes[2].grid(alpha=0.3, axis='y')

# Plot 4: Action composition
action_data = results_df.groupby('policy')[['n_surveys', 'n_drills']].mean()
action_data.plot(kind='bar', stacked=True, ax=axes[3], 
                 color=['lightblue', 'orange'], alpha=0.7)
axes[3].set_ylabel('Average Number of Actions', fontsize=11)
axes[3].set_title('Action Composition by Policy', fontsize=12, fontweight='bold')
axes[3].set_xticklabels(POLICIES, rotation=0)
axes[3].legend(['Surveys', 'Drills'])
axes[3].grid(alpha=0.3, axis='y')

plt.tight_layout()
fig1_path = f'{OUTPUT_DIR}/figure1_policy_comparison.png'
plt.savefig(fig1_path, dpi=300, bbox_inches='tight')
plt.close()

# Figure 2: Performance by Location
fig2, axes = plt.subplots(3, 1, figsize=(8, 12)) 

for idx, location in enumerate(df['location'].unique()):
    loc_data = results_df[results_df['location'] == location]
    
    # Box plot of rewards by policy
    data_to_plot = [loc_data[loc_data['policy'] == p]['total_reward'].values 
                    for p in POLICIES]
    
    bp = axes[idx].boxplot(data_to_plot, labels=POLICIES, patch_artist=True)
    
    # Color boxes
    policy_colors = ['lightgray', 'lightblue', 'lightgreen']
    for patch, color in zip(bp['boxes'], policy_colors):
        patch.set_facecolor(color)
    
    axes[idx].set_ylabel('Total Reward', fontsize=11)
    axes[idx].set_title(f'{location.title()}', fontsize=12, fontweight='bold')
    axes[idx].grid(alpha=0.3, axis='y')
    axes[idx].axhline(y=0, color='red', linestyle='--', alpha=0.3)

plt.tight_layout()
fig2_path = f'{OUTPUT_DIR}/figure2_location_comparison.png'
plt.savefig(fig2_path, dpi=300, bbox_inches='tight')
print(f"Saved Figure 2: {fig2_path}")
plt.close()


# Summary

print("\nKey Results:")
for policy in POLICIES:
    policy_data = results_df[results_df['policy'] == policy]
    print(f"  {policy.upper()}:")
    print(f"    Mean reward: {policy_data['total_reward'].mean():.1f} ± {policy_data['total_reward'].std():.1f}")
    print(f"    Mean discoveries: {policy_data['n_discoveries'].mean():.2f} ± {policy_data['n_discoveries'].std():.2f}")
    print(f"    Discovery rate: {policy_data['discovery_rate'].mean():.3f}")
