import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import axios from 'axios';

const Onboarding: React.FC = () => {
    const [pic, setPic] = useState<File | null>(null);
    const [doc, setDoc] = useState<File | null>(null);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();

    const handleFileChange = (setter: React.Dispatch<React.SetStateAction<File | null>>) => (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setter(e.target.files[0]);
        }
    };

    const handleSkip = async () => {
        try {
            await api.post('/onboarding/upload', null, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setMessage("Skipping setup... Redirecting...");
            setTimeout(() => navigate('/dashboard'), 1000);
        } catch (err) {
            console.error(err);
            setError("Failed to skip onboarding");
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setMessage('');

        const formData = new FormData();
        if (pic) formData.append('energy_pic', pic);
        if (doc) formData.append('doc', doc);

        try {
            await api.post('/onboarding/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setMessage("Onboarding complete! Redirecting...");
            setTimeout(() => navigate('/dashboard'), 1500);
        } catch (err) {
            if (axios.isAxiosError(err)) {
                setError(err.response?.data?.detail || 'Upload failed');
            } else {
                setError('An unexpected error occurred');
            }
        }
    };

    return (
        <div className="container" style={{ maxWidth: '600px', marginTop: '4rem' }}>
            <div className="card">
                <h2 style={{ textAlign: 'center' }}>Complete Your Setup</h2>
                <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    Please upload a picture of your energy source and a supporting document.
                    <br />
                    <small>(This step is optional, you can skip it for now)</small>
                </p>

                {error && <div className="error-msg">{error}</div>}
                {message && <div style={{ color: 'var(--primary)', textAlign: 'center' }}>{message}</div>}

                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '2rem' }}>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Energy Source Picture (Image)</label>
                        <input type="file" accept="image/*" onChange={handleFileChange(setPic)} />
                    </div>
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem' }}>Supporting Document (PDF/Image)</label>
                        <input type="file" accept="image/*,application/pdf" onChange={handleFileChange(setDoc)} />
                    </div>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <button type="submit" style={{ flex: 1 }}>Submit Documents</button>
                        <button type="button" onClick={handleSkip} style={{ flex: 1, backgroundColor: 'var(--secondary)', color: 'var(--text)' }}>Skip for Now</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Onboarding;
