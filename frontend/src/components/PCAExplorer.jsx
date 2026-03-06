import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Cell, ZAxis } from 'recharts';
import { Network } from 'lucide-react';

const PCAExplorer = ({ features = [], beliefs = [], onCellSelect, selectedCellIdx }) => {

    if (!features || features.length === 0) return null;

    // Prepare scatter data
    const scatterData = features.map(f => {
        const idx = f.cell_idx;
        const belief = beliefs[idx] !== undefined ? beliefs[idx] : 0.2;
        return {
            ...f,
            belief: belief, // For sizing
            // ZAxis mapping ranges 
            z: belief,
        };
    });

    // Separate by cluster for legends/colors
    const cluster0 = scatterData.filter(d => d.cluster === 0);
    const cluster1 = scatterData.filter(d => d.cluster === 1);

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-slate-800 border border-slate-600 p-3 rounded shadow-lg text-xs font-mono z-50">
                    <div className="font-bold text-white mb-1 flex justify-between">
                        <span>Cell #{data.cell_idx}</span>
                    </div>
                    <p className="text-slate-400">Cluster: <span className="text-white">{data.cluster}</span></p>
                    <p className="text-slate-400">PC1: <span className="text-white">{data.pca_feature_1.toFixed(3)}</span></p>
                    <p className="text-slate-400">PC2: <span className="text-white">{data.pca_feature_2.toFixed(3)}</span></p>
                    <p className="text-slate-400">Belief: <span className="text-yellow-400">{(data.belief * 100).toFixed(1)}%</span></p>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-[#1e212b] border border-slate-800 rounded-lg p-5 shadow-sm h-[400px] flex flex-col">
            <div className="flex items-center gap-2 mb-4">
                <Network className="text-indigo-400" size={18} />
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">PCA Feature Explorer</h3>
                <span className="ml-auto text-xs text-slate-500">PC1 vs PC2</span>
            </div>

            <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 10, right: 10, bottom: 20, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                        <XAxis
                            type="number"
                            dataKey="pca_feature_1"
                            name="PC1"
                            stroke="#64748b"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            type="number"
                            dataKey="pca_feature_2"
                            name="PC2"
                            stroke="#64748b"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                        />
                        <ZAxis type="number" dataKey="z" range={[20, 200]} name="belief" />
                        <RechartsTooltip content={<CustomTooltip />} cursor={{ strokeDasharray: '3 3' }} />

                        {/* Render Cluster 0 */}
                        <Scatter name="Cluster 0" data={cluster0} onClick={(e) => onCellSelect && onCellSelect(e.payload)}>
                            {cluster0.map((entry, index) => (
                                <Cell
                                    key={`c0-${index}`}
                                    fill={selectedCellIdx === entry.cell_idx ? '#ffffff' : '#64748b'}
                                    opacity={selectedCellIdx === entry.cell_idx ? 1 : 0.6}
                                    stroke={selectedCellIdx === entry.cell_idx ? '#00d4aa' : 'transparent'}
                                    strokeWidth={selectedCellIdx === entry.cell_idx ? 2 : 0}
                                    style={{ cursor: 'pointer' }}
                                />
                            ))}
                        </Scatter>

                        {/* Render Cluster 1 */}
                        <Scatter name="Cluster 1" data={cluster1} onClick={(e) => onCellSelect && onCellSelect(e.payload)}>
                            {cluster1.map((entry, index) => (
                                <Cell
                                    key={`c1-${index}`}
                                    fill={selectedCellIdx === entry.cell_idx ? '#ffffff' : '#00d4aa'}
                                    opacity={selectedCellIdx === entry.cell_idx ? 1 : 0.8}
                                    stroke={selectedCellIdx === entry.cell_idx ? '#ffffff' : 'transparent'}
                                    strokeWidth={selectedCellIdx === entry.cell_idx ? 2 : 0}
                                    style={{ cursor: 'pointer' }}
                                />
                            ))}
                        </Scatter>
                    </ScatterChart>
                </ResponsiveContainer>
            </div>
            <div className="flex justify-center gap-4 mt-2 text-xs text-slate-500">
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-slate-500"></div> Cluster 0</div>
                <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[#00d4aa]"></div> Cluster 1</div>
                <div className="ml-4 text-[10px] italic">Size encodes current belief</div>
            </div>
        </div>
    );
};

export default PCAExplorer;
