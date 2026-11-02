import React, { useState } from 'react';
import IntakeForm from './components/IntakeForm';
import DiagnosticView from './components/DiagnosticView';
import SymptomSelector from './components/SymptomSelector';
import { submitPatientIntake } from './services/api';

export default function App() {
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    const handleFormSubmit = async (payload) => {
        setLoading(true);
        try {
            const data = await submitPatientIntake(payload);
            setResult(data);
        } catch (error) {
            alert('Failed to connect to the backend service.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 p-8">
            <div className="max-w-2xl mx-auto">
                <header className="mb-8 text-center">
                    <h1 className="text-3xl font-extrabold text-blue-900">PharmAI Desktop Client</h1>
                    <p className="text-sm text-gray-600">AI-Driven Clinical Diagnosis and Medication Guidance</p>
                </header>
                <SymptomSelector/>
                <IntakeForm onSubmit={handleFormSubmit} loading={loading} />
                <DiagnosticView result={result} />
            </div>
        </div>
    );
}