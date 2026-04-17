import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Activity, Brain, Code, AlertTriangle, Info, Moon } from 'lucide-react';
import clsx from 'clsx';
import { format } from 'date-fns';

const API_URL = "http://localhost:8000/api";

type Insight = {
  level: 'CRITICAL' | 'WARNING' | 'INFO';
  message: string;
};

type APIResponse = {
  insights: Insight[];
  tomorrow_prediction: number;
};

type LogData = {
  id: number;
  date: string;
  sleep_hours: number;
  mood_score: number;
  total_coding_minutes: number;
  productivity_score: number;
};

const Dashboard = () => {
    const [insightsData, setInsightsData] = useState<APIResponse | null>(null);
    const [logs, setLogs] = useState<LogData[]>([]);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [insightsRes, logsRes] = await Promise.all([
                axios.get(`${API_URL}/insights`),
                axios.get(`${API_URL}/logs`)
            ]);
            setInsightsData(insightsRes.data);
            setLogs(logsRes.data);
        } catch (error) {
            console.error("Backend error, loading mock state for dev:", error);
            setInsightsData({
                insights: [
                    {level: "CRITICAL", message: "Poor sleep is killing your output. You ship 19.5% less code after late nights."},
                    {level: "WARNING", message: "You spent 2.5 hours on distractions recently. That's a 'death by a thousand tabs' reality."}
                ],
                tomorrow_prediction: 43
            });
            setLogs([
                {id: 0, date: "2026-04-10", sleep_hours: 5.0, mood_score: 2, total_coding_minutes: 110, productivity_score: 41},
                {id: 1, date: "2026-04-11", sleep_hours: 7.2, mood_score: 4, total_coding_minutes: 240, productivity_score: 82},
                {id: 2, date: "2026-04-12", sleep_hours: 6.8, mood_score: 3, total_coding_minutes: 210, productivity_score: 75},
                {id: 3, date: "2026-04-13", sleep_hours: 8.0, mood_score: 5, total_coding_minutes: 280, productivity_score: 91},
                {id: 4, date: "2026-04-14", sleep_hours: 4.5, mood_score: 2, total_coding_minutes: 90,  productivity_score: 28},
                {id: 5, date: "2026-04-15", sleep_hours: 5.5, mood_score: 2, total_coding_minutes: 120, productivity_score: 35},
                {id: 6, date: "2026-04-16", sleep_hours: 7.5, mood_score: 4, total_coding_minutes: 240, productivity_score: 85}
            ]);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-8">
            <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-500 font-sans tracking-tight">
                        Personal Analytics
                    </h1>
                    <p className="text-zinc-400 mt-2 text-lg">Brutally honest developer metrics.</p>
                </div>
            </header>

            {insightsData && insightsData.insights.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Brain className="w-5 h-5 text-primary" />
                        AI Diagnostics
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        {insightsData.insights.map((insight, idx) => (
                            <div key={idx} className={clsx(
                                "p-5 rounded-2xl border flex items-start gap-4 backdrop-blur-md relative overflow-hidden transition-all duration-300 hover:shadow-lg",
                                insight.level === 'CRITICAL' ? "bg-danger/10 border-danger/20 text-danger-400 hover:shadow-danger/10" :
                                insight.level === 'WARNING' ? "bg-warning/10 border-warning/20 text-warning-400 hover:shadow-warning/10" :
                                "bg-primary/10 border-primary/20 text-primary-400 hover:shadow-primary/10"
                            )}>
                                {insight.level === 'CRITICAL' ? <AlertTriangle className="w-6 h-6 shrink-0 text-danger mt-1" /> :
                                 insight.level === 'WARNING' ? <AlertTriangle className="w-6 h-6 shrink-0 text-warning mt-1" /> :
                                 <Info className="w-6 h-6 shrink-0 text-primary mt-1" />}
                                <div>
                                    <h3 className="font-semibold text-zinc-100 text-lg mb-1">{insight.level}</h3>
                                    <p className="opacity-90 leading-relaxed">{insight.message}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid md:grid-cols-3 gap-6">
                 {/* Prediction Card */}
                 <div className="brutal-card p-6 md:col-span-1 flex flex-col justify-center">
                     <h3 className="text-zinc-400 font-medium mb-6 flex items-center gap-2 uppercase tracking-wider text-sm">
                         <Activity className="w-4 h-4 text-emerald-400" /> 
                         Predicted Efficiency
                     </h3>
                     <div className="text-7xl font-bold flex items-baseline gap-2 tabular-nums">
                         {insightsData?.tomorrow_prediction || 0}
                         <span className="text-2xl text-zinc-600 font-normal">/ 100</span>
                     </div>
                     <p className="text-sm text-zinc-500 mt-6 pt-4 border-t border-zinc-800">Based on currect trajectory and models estimating sleep debt impact.</p>
                 </div>

                 {/* Chart Card */}
                 <div className="glass-panel p-6 md:col-span-2 relative">
                     <h3 className="text-zinc-100 font-semibold mb-6 flex items-center gap-2">
                         <Code className="w-5 h-5 text-primary"/>
                         Productivity vs Sleep
                     </h3>
                     <div className="h-72 w-full">
                         <ResponsiveContainer width="100%" height="100%">
                             <LineChart data={logs} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                                 <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                                 <XAxis 
                                    dataKey="date" 
                                    stroke="#71717a" 
                                    tickFormatter={(val) => {
                                        try { return format(new Date(val), 'MMM d'); } catch { return val; }
                                    }}
                                    tick={{fontSize: 12}}
                                    tickLine={false}
                                    axisLine={false}
                                    dy={10}
                                 />
                                 <YAxis yAxisId="left" stroke="#71717a" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                                 <YAxis yAxisId="right" orientation="right" stroke="#71717a" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                                 <Tooltip 
                                    contentStyle={{backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'}}
                                    itemStyle={{color: '#e4e4e7'}}
                                 />
                                 <Line yAxisId="left" type="monotone" dataKey="productivity_score" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 8, stroke: '#60a5fa'}} name="Productivity" />
                                 <Line yAxisId="right" type="monotone" dataKey="sleep_hours" stroke="#10b981" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 8, stroke: '#34d399'}} name="Sleep (hrs)" />
                             </LineChart>
                         </ResponsiveContainer>
                     </div>
                 </div>
            </div>
            
            <div className="glass-panel p-1 border-white/5 line-clamp-none overflow-hidden">
             <div className="bg-surface/50 rounded-xl p-6">
                <h3 className="text-zinc-100 font-semibold mb-6 flex items-center gap-2">
                    <Moon className="w-5 h-5 text-indigo-400"/>
                    Raw Logs
                </h3>
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left text-zinc-400">
                        <thead className="text-xs uppercase bg-surfaceHighlight/50 text-zinc-300">
                            <tr>
                                <th className="px-6 py-4 rounded-tl-lg font-medium">Date</th>
                                <th className="px-6 py-4 font-medium">Sleep</th>
                                <th className="px-6 py-4 font-medium">Coding Time</th>
                                <th className="px-6 py-4 rounded-tr-lg font-medium">Productivity</th>
                            </tr>
                        </thead>
                        <tbody>
                            {logs.map((log) => (
                                <tr key={log.id} className="border-b border-zinc-800/50 hover:bg-surfaceHighlight/30 transition-colors">
                                    <td className="px-6 py-4 text-zinc-200">
                                        {(() => {
                                            try {
                                                return format(new Date(log.date), 'MMM d, yyyy');
                                            } catch (e) {
                                                return log.date;
                                            }
                                        })()}
                                    </td>
                                    <td className="px-6 py-4 tabular-nums text-zinc-300">{log.sleep_hours} hrs</td>
                                    <td className="px-6 py-4 tabular-nums text-zinc-300">{Math.floor(log.total_coding_minutes / 60)}h {log.total_coding_minutes % 60}m</td>
                                    <td className="px-6 py-4">
                                        <div className="w-full bg-zinc-800 rounded-full h-2 shadow-inner overflow-hidden">
                                            <div className={clsx(
                                                "h-2 rounded-full transition-all duration-1000",
                                                log.productivity_score > 70 ? "bg-success" : log.productivity_score > 40 ? "bg-warning" : "bg-danger"
                                            )} style={{width: `${log.productivity_score}%`}}></div>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
              </div>
            </div>
        </div>
    );
};

export default Dashboard;
