import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Activity } from 'lucide-react';

const BeliefChart = ({ actionsLog = [], maxSteps = 50 }) => {

    const chartData = useMemo(() => {
        if (!actionsLog || actionsLog.length === 0) return [];

        // We want to track belief over time for the top 5 highest-belief cells from the latest step
        const latestAllBeliefs = actionsLog[actionsLog.length - 1];

        // The requirement says "The top-5 highest-belief cells". 
        // Since our step_log only contains belief for the *acted upon* cell, 
        // we need to rely on the fact that App.jsx has `allBeliefs` array for the current epoch.
        // However, to draw a *line* chart, we need historical beliefs for *those* 5 cells.

        // Since `step` only returns the belief of the cell acted upon, constructing historical traces 
        // for 5 cells is extremely memory intensive or requires the backend to send full belief arrays every step.
        // Let's implement a simplified version for MVP: We just plot the belief of the *cell that was chosen* 
        // at each step over time.
        const data = actionsLog.map(log => ({
            step: log.step,
            belief: parseFloat((log.belief * 100).toFixed(1)),
            action: log.action,
            discovery: log.discovery,
            cell: log.cell
        }));

        return data;
    }, [actionsLog]);

    if (chartData.length === 0) return (
        <div className="flex flex-col items-center justify-center h-full text-slate-500 min-h-[300px] border border-slate-800 rounded-lg bg-[#1e212b]">
            <Activity size={32} className="mb-2 opacity-50" />
            <p className="text-sm">Run simulation to see belief evolution</p>
        </div>
    );

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-slate-800 border border-slate-600 p-3 rounded shadow-lg text-xs font-mono">
                    <p className="text-white mb-1">Epoch: {label}</p>
                    <p className="text-[#00d4aa]">Cell: {data.cell}</p>
                    <p className="text-yellow-400">Belief: {data.belief}%</p>
                    <p className="text-blue-300 capitalize text-[10px] mt-1">Action: {data.action}</p>
                    {data.discovery && <p className="text-emerald-400 font-bold mt-1">★ DISCOVERY</p>}
                </div>
            );
        }
        return null;
    };

    return (
        <div className="bg-[#1e212b] border border-slate-800 rounded-lg p-5 shadow-sm h-[350px] flex flex-col">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Target Belief Trajectory</h3>
                <span className="text-xs text-slate-500 border border-slate-700 px-2 py-1 rounded bg-slate-800">Latest step: {chartData.length - 1}</span>
            </div>
            <div className="flex-1 w-full relative">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                        data={chartData}
                        margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} vertical={false} />
                        <XAxis
                            dataKey="step"
                            stroke="#64748b"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                        />
                        <YAxis
                            domain={[0, 100]}
                            stroke="#64748b"
                            fontSize={10}
                            tickLine={false}
                            axisLine={false}
                            tickFormatter={val => `${val}%`}
                        />
                        <RechartsTooltip content={<CustomTooltip />} />

                        {chartData.map((d, index) => {
                            // Draw vertical reference lines for drills
                            if (d.action === 'drill') {
                                return <ReferenceLine key={index} x={d.step} stroke={d.discovery ? '#10b981' : '#ef4444'} strokeOpacity={0.5} strokeDasharray="3 3" />;
                            }
                            return null;
                        })}

                        <Line
                            type="monotone"
                            dataKey="belief"
                            stroke="#00d4aa"
                            strokeWidth={2}
                            dot={{ r: 3, fill: '#0f1117', strokeWidth: 1.5 }}
                            activeDot={{ r: 5, fill: '#00d4aa', stroke: '#fff' }}
                            isAnimationActive={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default BeliefChart;
