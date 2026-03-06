import React from 'react';
import { Settings } from 'lucide-react';

const Slider = ({ label, name, value, min, max, step, onChange, unit = '', disabled, labelColor = 'text-slate-400' }) => (
    <div>
        <div className="flex justify-between items-center mb-2">
            <label className={`text-xs ${labelColor} uppercase font-medium`}>{label}</label>
            <span className="text-sm font-mono text-white">{unit}{value}</span>
        </div>
        <input
            type="range"
            name={name}
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={onChange}
            disabled={disabled}
            className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-[#00d4aa] disabled:opacity-50"
        />
        <div className="flex justify-between mt-1 text-[10px] text-slate-500 font-mono">
            <span>{unit}{min}</span>
            <span>{unit}{max}</span>
        </div>
    </div>
);

const ConfigPanel = ({ config, onConfigChange, disabled }) => {
    const regions = ['Namibia', 'Australia', 'Mali', 'All Three'];
    const policies = [
        { id: 'ucb', label: 'UCB (Upper Confidence Bound)' },
        { id: 'greedy', label: 'Greedy' },
        { id: 'random', label: 'Random' }
    ];

    const handleChange = (e) => {
        const { name, value, type } = e.target;
        onConfigChange({
            [name]: type === 'number' || type === 'range' ? parseFloat(value) : value
        });
    };

    return (
        <div className="p-5 flex flex-col h-full overflow-y-auto">
            <div className="flex items-center gap-2 mb-6">
                <Settings className="text-slate-400" size={18} />
                <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Parameters</h2>
            </div>

            <div className="flex flex-col gap-5">

                {/* Region Selection */}
                <div>
                    <label className="block text-xs text-slate-400 mb-2 uppercase font-medium">Region</label>
                    <select
                        name="region"
                        value={config.region}
                        onChange={handleChange}
                        disabled={disabled}
                        className="w-full bg-[#1e212b] border border-slate-700 rounded-md p-2.5 text-sm text-white focus:ring-1 focus:ring-[#00d4aa] focus:border-[#00d4aa] outline-none disabled:opacity-50"
                    >
                        {regions.map(r => <option key={r} value={r}>{r}</option>)}
                    </select>
                </div>

                {/* Policy Selection */}
                <div>
                    <label className="block text-xs text-slate-400 mb-2 uppercase font-medium">Policy</label>
                    <select
                        name="policy"
                        value={config.policy}
                        onChange={handleChange}
                        disabled={disabled}
                        className="w-full bg-[#1e212b] border border-slate-700 rounded-md p-2.5 text-sm text-white focus:ring-1 focus:ring-[#00d4aa] focus:border-[#00d4aa] outline-none disabled:opacity-50"
                    >
                        {policies.map(p => <option key={p.id} value={p.id}>{p.label}</option>)}
                    </select>
                </div>

                {/* Budget Slider */}
                <Slider
                    label="Budget"
                    name="budget"
                    min={1000} max={10000} step={500}
                    value={config.budget}
                    onChange={handleChange}
                    unit="$"
                    disabled={disabled}
                />

                {/* Steps */}
                <div>
                    <div className="flex justify-between items-center mb-2">
                        <label className="text-xs text-slate-400 uppercase font-medium">Steps (Play)</label>
                        <span className="text-sm font-mono text-white">{config.steps}</span>
                    </div>
                    <input
                        type="range"
                        name="steps"
                        min={1}
                        max={100}
                        step={1}
                        value={config.steps}
                        onChange={handleChange}
                        className="w-full h-1.5 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-indigo-400"
                    />
                    <div className="flex justify-between mt-1 text-[10px] text-slate-500 font-mono">
                        <span>1</span>
                        <span>100</span>
                    </div>
                </div>

                {/* UCB Constant */}
                {config.policy === 'ucb' && (
                    <Slider
                        label="UCB Constant (c)"
                        name="exploration_constant"
                        min={0.1} max={5.0} step={0.1}
                        value={config.exploration_constant}
                        onChange={handleChange}
                        labelColor="text-blue-400"
                    />
                )}

                {/* Action Costs Section */}
                <div className="border-t border-slate-700/60 pt-4">
                    <p className="text-xs text-slate-400 uppercase font-semibold mb-4 tracking-wider">Action Costs</p>

                    <div className="flex flex-col gap-4">
                        <Slider
                            label="Survey Cost ($)"
                            name="cost_survey"
                            min={0} max={1000} step={50}
                            value={config.cost_survey}
                            onChange={handleChange}
                            unit="$"
                            disabled={disabled}
                            labelColor="text-blue-300"
                        />

                        <Slider
                            label="Drill Success Cost ($)"
                            name="cost_drill_success"
                            min={0} max={1000} step={50}
                            value={config.cost_drill_success}
                            onChange={handleChange}
                            unit="$"
                            disabled={disabled}
                            labelColor="text-emerald-300"
                        />

                        <Slider
                            label="Drill Fail Cost ($)"
                            name="cost_drill_fail"
                            min={0} max={1000} step={50}
                            value={config.cost_drill_fail}
                            onChange={handleChange}
                            unit="$"
                            disabled={disabled}
                            labelColor="text-red-300"
                        />
                    </div>
                </div>

                {disabled && (
                    <div className="p-3 bg-blue-900/20 border border-blue-800/50 rounded-lg text-xs leading-relaxed text-blue-300">
                        Reset simulation to change configuration.
                    </div>
                )}
            </div>
        </div>
    );
};

export default ConfigPanel;
