# Chasing Fairy Circles

Geologic hydrogen represents a promising carbon-free energy source, yet exploration remains challenging due to the lack surveys and high drilling costs. In this project, we aim to describe geologic hydrogen exploration as a Partially Observable Markov Decision Process (POMDP), where our agent must efficiently allocate survey resources across potential drilling sites using noisy geophysical observations. By introducing the use of Google Earth Engine satellite data (Sentinel-2, Landsat 8, SRTM) across three known fairy circle regions (Namibia, Australia, Mali), we extract 13 multispectral and topographic features reduced to 5 principal components via PCA. We implement three online planning policies-random baseline, greedy heuristic search, and Upper Confidence Bound (UCB), and we evaluate their performance under budget constraints. 

## Project Structure
chaisingfairycircles
  gee_data_extractor.py   Data extraction from GEE
  feature_prep.py         PCA and feature engineering
  environment.py          FCEnvironment class
  pomdp_agent.py          POMDPAgent with policies
  main.py                 Run experiments
  README.md               Project documentation
