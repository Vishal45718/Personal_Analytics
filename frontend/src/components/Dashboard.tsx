import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar } from 'recharts';
import { Activity, Brain, Code, AlertTriangle, Info, Moon, TrendingUp, Clock, Zap } from 'lucide-react';
import clsx from 'clsx';
import { format } from 'date-fns';

const API_URL = "http://localhost:8000/api";

type Insight = {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  category: string;
  title: string;
  body: string;
  data?: any;
};

type APIResponse = {
  insights: Insight[];
  tomorrow_prediction: number;
};

type LogData = {
  id: number;
  date: string;
  sleep_start: string | null;
  sleep_end: string | null;
  sleep_duration_min: number | null;
  sleep_quality: number | null;
  deep_sleep_pct: number | null;
  mood_score: number | null;
  notes: string | null;
  sessions: Array<{
    id: number;
    category: string;
    app_name: string;
    duration_seconds: number;
    started_at: string;
    ended_at: string;
    is_distraction: boolean;
    focus_depth_score: number | null;
    source: string;
  }>;
};

type AnalyticsSummary = {
  logs_summary: {
    avg_sleep_min: number;
    avg_mood: number;
    avg_sleep_quality: number;
    total_days: number;
  };
  productivity_trend: Array<{
    date: string;
    productivity_score: number;
    coding_minutes: number;
    distraction_minutes: number;
    total_minutes: number;
  }>;
  wasted_time: {
    daily_wasted: any;
    avg_wasted_min: number;
    human_readable: string;
  };
};

const Dashboard = () => {
    const [insightsData, setInsightsData] = useState<APIResponse | null>(null);
    const [logs, setLogs] = useState<LogData[]>([]);
    const [analyticsSummary, setAnalyticsSummary] = useState<AnalyticsSummary | null>(null);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [insightsRes, logsRes, analyticsRes] = await Promise.all([
                axios.get(`${API_URL}/insights`),
                axios.get(`${API_URL}/logs`),
                axios.get(`${API_URL}/analytics/summary`)
            ]);
            setInsightsData(insightsRes.data);
            setLogs(logsRes.data);
            setAnalyticsSummary(analyticsRes.data);
        } catch (error) {
            console.error("Backend error, loading mock state for dev:", error);
            setInsightsData({
                insights: [
                    {id: "1", severity: "critical", category: "sleep", title: "Chronic sleep debt detected", body: "Poor sleep is costing you 23.5% productivity. Your output drops from 78.2 to 54.7 after bad nights."},
                    {id: "2", severity: "warning", category: "productivity", title: "Post-11PM work is mostly theater", body: "Your focus depth drops 31% after 11 PM vs your 9-5 window"}
                ],
                tomorrow_prediction: 43
            });
            setLogs([
                {id: 0, date: "2026-04-10", sleep_start: null, sleep_end: null, sleep_duration_min: 300, sleep_quality: 2, deep_sleep_pct: 12.5, mood_score: 2, notes: "Tired day", sessions: []},
                {id: 1, date: "2026-04-11", sleep_start: null, sleep_end: null, sleep_duration_min: 450, sleep_quality: 4, deep_sleep_pct: 22.1, mood_score: 4, notes: "Good rest", sessions: []},
                {id: 2, date: "2026-04-12", sleep_start: null, sleep_end: null, sleep_duration_min: 420, sleep_quality: 3, deep_sleep_pct: 18.3, mood_score: 3, notes: "Okay", sessions: []},
                {id: 3, date: "2026-04-13", sleep_start: null, sleep_end: null, sleep_duration_min: 480, sleep_quality: 5, deep_sleep_pct: 24.7, mood_score: 5, notes: "Excellent", sessions: []},
                {id: 4, date: "2026-04-14", sleep_start: null, sleep_end: null, sleep_duration_min: 270, sleep_quality: 2, deep_sleep_pct: 8.9, mood_score: 2, notes: "Bad night", sessions: []},
                {id: 5, date: "2026-04-15", sleep_start: null, sleep_end: null, sleep_duration_min: 330, sleep_quality: 2, deep_sleep_pct: 11.2, mood_score: 2, notes: "Still tired", sessions: []},
                {id: 6, date: "2026-04-16", sleep_start: null, sleep_end: null, sleep_duration_min: 450, sleep_quality: 4, deep_sleep_pct: 21.8, mood_score: 4, notes: "Better", sessions: []}
            ]);
        }
    };

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8">
            <header className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-500 font-sans tracking-tight">
                        Personal Analytics
                    </h1>
                    <p className="text-zinc-400 mt-2 text-lg">Brutally honest developer metrics.</p>
                </div>
                {analyticsSummary && (
                    <div className="flex gap-6 text-sm">
                        <div className="text-center">
                            <div className="text-2xl font-bold text-emerald-400">{Math.floor(analyticsSummary.logs_summary.avg_sleep_min / 60)}h {analyticsSummary.logs_summary.avg_sleep_min % 60}m</div>
                            <div className="text-zinc-500">Avg Sleep</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-blue-400">{analyticsSummary.logs_summary.avg_mood.toFixed(1)}</div>
                            <div className="text-zinc-500">Avg Mood</div>
                        </div>
                        <div className="text-center">
                            <div className="text-2xl font-bold text-purple-400">{analyticsSummary.wasted_time.avg_wasted_min.toFixed(0)}m</div>
                            <div className="text-zinc-500">Daily Waste</div>
                        </div>
                    </div>
                )}
            </header>

            {insightsData && insightsData.insights.length > 0 && (
                <div className="space-y-4">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <Brain className="w-5 h-5 text-red-400" />
                        AI Diagnostics
                    </h2>
                    <div className="grid gap-4 md:grid-cols-2">
                        {insightsData.insights.map((insight, idx) => (
                            <div key={insight.id || idx} className={clsx(
                                "p-5 rounded-2xl border flex items-start gap-4 backdrop-blur-md relative overflow-hidden transition-all duration-300 hover:shadow-lg",
                                insight.severity === 'critical' ? "bg-red-500/10 border-red-500/20 text-red-400 hover:shadow-red-500/10" :
                                insight.severity === 'warning' ? "bg-yellow-500/10 border-yellow-500/20 text-yellow-400 hover:shadow-yellow-500/10" :
                                "bg-blue-500/10 border-blue-500/20 text-blue-400 hover:shadow-blue-500/10"
                            )}>
                                {insight.severity === 'critical' ? <AlertTriangle className="w-6 h-6 shrink-0 text-red-400 mt-1" /> :
                                 insight.severity === 'warning' ? <AlertTriangle className="w-6 h-6 shrink-0 text-yellow-400 mt-1" /> :
                                 <Info className="w-6 h-6 shrink-0 text-blue-400 mt-1" />}
                                <div>
                                    <h3 className="font-semibold text-zinc-100 text-lg mb-1">{insight.title}</h3>
                                    <p className="opacity-90 leading-relaxed">{insight.body}</p>
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
                     <p className="text-sm text-zinc-500 mt-6 pt-4 border-t border-zinc-800">Based on current trajectory and sleep debt analysis.</p>
                 </div>

                 {/* Productivity Chart */}
                 <div className="glass-panel p-6 md:col-span-2 relative">
                     <h3 className="text-zinc-100 font-semibold mb-6 flex items-center gap-2">
                         <TrendingUp className="w-5 h-5 text-blue-400"/>
                         Productivity Trend
                     </h3>
                     <div className="h-72 w-full">
                         {analyticsSummary ? (
                             <ResponsiveContainer width="100%" height="100%">
                                 <LineChart data={analyticsSummary.productivity_trend} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
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
                                     <YAxis yAxisId="left" stroke="#71717a" tick={{fontSize: 12}} tickLine={false} axisLine={false} domain={[0, 100]} />
                                     <YAxis yAxisId="right" orientation="right" stroke="#71717a" tick={{fontSize: 12}} tickLine={false} axisLine={false} />
                                     <Tooltip
                                        contentStyle={{backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'}}
                                        itemStyle={{color: '#e4e4e7'}}
                                     />
                                     <Line yAxisId="left" type="monotone" dataKey="productivity_score" stroke="#3b82f6" strokeWidth={3} dot={{r: 4, strokeWidth: 2}} activeDot={{r: 8, stroke: '#60a5fa'}} name="Productivity" />
                                     <Line yAxisId="right" type="monotone" dataKey="coding_minutes" stroke="#10b981" strokeWidth={2} dot={{r: 3, strokeWidth: 1}} name="Coding (min)" />
                                 </LineChart>
                             </ResponsiveContainer>
                         ) : (
                             <div className="flex items-center justify-center h-full text-zinc-500">
                                 <Clock className="w-8 h-8 mr-2" />
                                 Loading analytics...
                             </div>
                         )}
                     </div>
                 </div>
            </div>

            {/* Activity Breakdown */}
            {analyticsSummary && (
                <div className="grid md:grid-cols-2 gap-6">
                    <div className="glass-panel p-6">
                        <h3 className="text-zinc-100 font-semibold mb-6 flex items-center gap-2">
                            <Zap className="w-5 h-5 text-yellow-400"/>
                            Time Distribution (Last 7 Days)
                        </h3>
                        <div className="space-y-4">
                            {analyticsSummary.productivity_trend.slice(-7).map((day, idx) => (
                                <div key={idx} className="flex items-center justify-between">
                                    <span className="text-sm text-zinc-400">
                                        {format(new Date(day.date), 'MMM d')}
                                    </span>
                                    <div className="flex gap-2 text-xs">
                                        <span className="text-green-400">{Math.floor(day.coding_minutes)}m coding</span>
                                        <span className="text-red-400">{Math.floor(day.distraction_minutes)}m waste</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="glass-panel p-6">
                        <h3 className="text-zinc-100 font-semibold mb-6 flex items-center gap-2">
                            <Moon className="w-5 h-5 text-indigo-400"/>
                            Sleep Quality Trend
                        </h3>
                        <div className="h-48">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={logs.slice(0, 7)} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#71717a"
                                        tickFormatter={(val) => {
                                            try { return format(new Date(val), 'MMM d'); } catch { return val; }
                                        }}
                                        tick={{fontSize: 10}}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis stroke="#71717a" tick={{fontSize: 10}} tickLine={false} axisLine={false} domain={[0, 5]} />
                                    <Tooltip
                                        contentStyle={{backgroundColor: '#18181b', border: '1px solid #27272a', borderRadius: '8px'}}
                                        labelFormatter={(val) => format(new Date(val), 'MMM d, yyyy')}
                                    />
                                    <Bar dataKey="sleep_quality" fill="#8b5cf6" radius={[2, 2, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            )}

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
                                <th className="px-6 py-4 font-medium">Quality</th>
                                <th className="px-6 py-4 font-medium">Mood</th>
                                <th className="px-6 py-4 rounded-tr-lg font-medium">Sessions</th>
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
                                    <td className="px-6 py-4 tabular-nums text-zinc-300">
                                        {log.sleep_duration_min ? `${Math.floor(log.sleep_duration_min / 60)}h ${log.sleep_duration_min % 60}m` : 'N/A'}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="w-full bg-zinc-800 rounded-full h-2 shadow-inner overflow-hidden">
                                            <div className={clsx(
                                                "h-2 rounded-full transition-all duration-1000",
                                                (log.sleep_quality || 0) >= 4 ? "bg-success" : (log.sleep_quality || 0) >= 3 ? "bg-warning" : "bg-danger"
                                            )} style={{width: `${((log.sleep_quality || 0) / 5) * 100}%`}}></div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 tabular-nums text-zinc-300">{log.mood_score || 'N/A'}/5</td>
                                    <td className="px-6 py-4 text-zinc-300">{log.sessions.length} sessions</td>
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
