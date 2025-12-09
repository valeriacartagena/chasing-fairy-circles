import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

# We want to transform raw GEE data into meaningful features suitable our POMDP model.
# We will use principal component analysis (PCA) for dimensionality reduction and feature extraction here!

df = pd.read_csv('gee_extracted_data.csv')
print(f"Original num of features: {df.shape[1]}")

metadata_cols = ['location', 'longitude', 'latitude']
feature_cols = [col for col in df.columns if col not in metadata_cols]
print(df[feature_cols].isnull().sum()) # To check if we have missing values

df[feature_cols] = df[feature_cols].fillna(df[feature_cols].mean())

# We will standardize the features before applying PCA
X = df[feature_cols].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Applying PCA
n_components = 5  # Choose number of features to keep
pca = PCA(n_components=n_components)
X_pca = pca.fit_transform(X_scaled)

variance = pca.explained_variance_ratio_ * 100
cumulative = np.cumsum(variance)

print("\nComponent  Variance(%)  Cumulative(%)")
print("-" * 40)
for i in range(5):
    print(f"PC{i+1}        {variance[i]:5.1f}       {cumulative[i]:5.1f}")


for i in range(n_components):
    df[f'pca_feature_{i+1}'] = X_pca[:, i]

df.to_csv('gee_features_pca.csv', index=False)
print(f"Number of features after PCA: {n_components}. Saved to 'gee_features_pca.csv'!")