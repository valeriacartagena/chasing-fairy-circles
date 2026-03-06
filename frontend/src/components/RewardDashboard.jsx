import React from 'react';
import { Target, Search, XCircle, Droplets, MapPin } from 'lucide-react';

const StatCard = ({ label, value, subtext, icon: Icon, colorClass }) => (
    <div className={`bg-[#1e212b] rounded-lg p-4 border border-slate-800 shadow-sm flex items-start gap-4 ${colorClass}`}>
        <div className={`p-3 rounded-md bg-opacity-20 flex-shrink-0 ${colorClass.replace('text-', 'bg-')}`}>
            <Icon size={20} className="currentColor" />
        </div>
        <div>
            <div className="text-sm text-slate-400 font-medium mb-1 uppercase tracking-wide">{label}</div>
            <div className="text-2xl font-bold font-mono text-slate-100">{value}</div>
            {subtext && <div className="text-xs text-slate-500 mt-1">{subtext}</div>}
        </div>
    </div>
);


const RewardDashboard = ({ budget, state }) => {
    const { stats, discoveries, budgetRemaining, stepLog, isDone } = state;

    const spent = budget - budgetRemaining;
    const spentPct = Math.min((spent / budget) * 100, 100);

    const totalDrills = stats ? stats.drills : 0;
    const discoveryRate = totalDrills > 0 ? ((discoveries / totalDrills) * 100).toFixed(1) : '0.0';

    return (
        <div className="flex flex-col gap-4">
            <div className="grid grid-cols-4 gap-4">

                <StatCard
                    label="Total Reward"
                    value={stats ? stats.totalReward : 0}
                    icon={Target}
                    colorClass="text-emerald-400"
                    subtext={isDone ? "Simulation Complete" : stepLog ? `Last action: ${stepLog.action}` : "Waiting to start"}
                />

                <div className="bg-[#1e212b] rounded-lg p-4 border border-slate-800 shadow-sm flex flex-col justify-center">
                    <div className="flex justify-between items-center mb-2">
                        <div className="text-sm text-slate-400 font-medium uppercase tracking-wide">Remaining Budget</div>
                        <div className="text-sm font-mono font-bold text-slate-200">${Math.round(budgetRemaining)} / ${budget}</div>
                    </div>
                    <div className="w-full bg-slate-900 rounded-full h-2.5 overflow-hidden">
                        <div
                            className={`h-2.5 rounded-full ${spentPct > 90 ? 'bg-red-500' : 'bg-[#00d4aa]'}`}
                            style={{ width: `${100 - spentPct}%` }}
                        ></div>
                    </div>
                    <div className="mt-2 text-xs text-slate-500 self-end">Spent: ${Math.round(spent)}</div>
                </div>

                <StatCard
                    label="Discoveries"
                    value={discoveries}
                    icon={Droplets}
                    colorClass="text-[#00d4aa]"
                    subtext={`${discoveryRate}% rate (of ${totalDrills} drillings)`}
                />

                <div className="bg-[#1e212b] rounded-lg p-4 border border-slate-800 shadow-sm">
                    <div className="text-sm text-slate-400 font-medium mb-3 uppercase tracking-wide">Actions</div>
                    <div className="flex items-end gap-2 text-sm text-slate-300">
                        <div className="flex items-center gap-1"><Search size={14} className="text-blue-400" /> {stats ? stats.surveys : 0}</div>
                        <div className="text-slate-600">|</div>
                        <div className="flex items-center gap-1"><MapPin size={14} className="text-teal-400" /> {totalDrills}</div>
                        <div className="text-slate-600">|</div>
                        <div className="flex items-center gap-1"><XCircle size={14} className="text-slate-400" /> {stats ? stats.ignores : 0}</div>
                    </div>
                    <div className="mt-2 w-full flex h-1.5 rounded-full overflow-hidden bg-slate-900">
                        {stats && (stats.surveys + totalDrills + stats.ignores) > 0 && (
                            <>
                                <div className="bg-blue-500" style={{ width: `${(stats.surveys / (stats.surveys + totalDrills + stats.ignores)) * 100}%` }}></div>
                                <div className="bg-teal-500" style={{ width: `${(totalDrills / (stats.surveys + totalDrills + stats.ignores)) * 100}%` }}></div>
                                <div className="bg-slate-500" style={{ flex: 1 }}></div>
                            </>
                        )}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default RewardDashboard;
