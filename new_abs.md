Autonomous exploration using drones presents a fundamental challenge across various applications.
While existing methods have made significant progress in exploration tasks within small-scale environments, they encounter difficulties in large-scale scene exploration due to inadequate viewpoint quality and boundary exploration.
This often results in excessively long flight paths and inefficient utilization of boundary information. 
In this paper, we propose a novel viewpoint generation scheme based on regional exploration, optimized by a global loss function associated with boundaries. 
Specifically, we first identify safe regions along the boundary and generate Gaussian-distributed viewpoints within these areas. 
Next, we divide the exploration area into multiple sub-regions and compute the traversal order for these regions to prioritize the exploration of critical areas. 
We employ a boundary gain mechanism to balance exploration across different regions, thereby reducing the backtracking phenomenon of drones during large-scale scene exploration. 
Experiments conducted in real-world environments demonstrate that the proposed method performs exceptionally well in complex settings, significantly enhancing exploration efficiency and improving the drone's autonomous exploration capabilities in large-scale scenarios.