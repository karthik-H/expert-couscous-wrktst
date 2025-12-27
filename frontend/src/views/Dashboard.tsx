import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import api from '../api/client';

interface EnergyData {
    id: number;
    timestamp: string;
    generated_energy: number;
}

const Dashboard: React.FC = () => {
    const [currentEnergy, setCurrentEnergy] = useState<number | null>(null);
    const [history, setHistory] = useState<EnergyData[]>([]);
    const navigate = useNavigate();

    const fetchData = async () => {
        try {
            const [currentRes, historyRes] = await Promise.all([
                api.get('/energy/current'),
                api.get('/energy/history')
            ]);
            setCurrentEnergy(currentRes.data.generated_energy);
            // Reverse history to show oldest to newest in chart
            setHistory(historyRes.data.reverse());
        } catch (e) {
            console.error("Error fetching data", e);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 60000); // Poll every minute
        return () => clearInterval(interval);
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('token');
        navigate('/login');
    };

    return (
        <div className="container">
            <div className="header">
                <h1>Energy Dashboard</h1>
                <button onClick={handleLogout} style={{ backgroundColor: '#ef4444' }}>Logout</button>
            </div>

            <div className="stat-grid">
                <div className="card">
                    <h3 style={{ margin: 0, color: 'var(--text-muted)' }}>Current Generation</h3>
                    <div style={{ fontSize: '2.5rem', fontWeight: 'bold', marginTop: '0.5rem', color: 'var(--primary)' }}>
                        {currentEnergy !== null ? `${currentEnergy.toFixed(2)} kWh` : 'Loading...'}
                    </div>
                </div>
            </div>

            <div className="card" style={{ height: '400px' }}>
                <h3>Generation History</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={history}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis
                            dataKey="timestamp"
                            tickFormatter={(tick) => new Date(tick).toLocaleTimeString()}
                            stroke="#9ca3af"
                        />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151' }}
                            labelFormatter={(label) => new Date(label).toLocaleString()}
                        />
                        <Line type="monotone" dataKey="generated_energy" stroke="#4ade80" strokeWidth={2} dot={false} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default Dashboard;
