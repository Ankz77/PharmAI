import { useState } from 'react';
import IntakeForm from './components/IntakeForm';
import DiagnosticView from './components/DiagnosticView';
import { submitPatientIntake } from './services/api';

export default function App() {
    const [diagnosticResult, setDiagnosticResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [diagnosisError, setDiagnosisError] = useState('');

    const handleIntakeSubmit = async (formData) => {
        setLoading(true);
        setDiagnosisError('');
        setDiagnosticResult(null);
        try {
            const response = await submitPatientIntake(formData);
            setDiagnosticResult(response);
        } catch (error) {
            console.error('Diagnosis evaluation failed', error);
            setDiagnosisError(error.response?.data?.detail || 'Unable to rank these symptoms. Please check the backend connection and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-100 text-slate-900">
            <header className="bg-blue-900 text-white py-4 px-4 sm:px-6 lg:px-8 shadow-md">
                <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
                    <h1 className="text-base sm:text-xl font-extrabold tracking-tight">PharmAI Clinical Decision Support</h1>
                    <span className="shrink-0 text-xs font-semibold bg-teal-600 px-3 py-1 rounded-full">Local Workspace</span>
                </div>
            </header>

            <main className="w-full max-w-7xl mx-auto p-4 sm:p-6">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6 items-start">
                    {/* Left Column: Intake Form */}
                    <div className="min-w-0 lg:col-span-5">
                        <IntakeForm onSubmit={handleIntakeSubmit} loading={loading} />
                    </div>

                    {/* Right Column: Diagnostic Results */}
                    <div className="min-w-0 lg:col-span-7">
                        {diagnosisError ? (
                            <div role="alert" className="rounded-xl border border-red-300 bg-red-50 p-5 text-sm text-red-800">
                                {diagnosisError}
                            </div>
                        ) : diagnosticResult ? (
                            <DiagnosticView result={diagnosticResult} />
                        ) : (
                            <div className="bg-white p-6 sm:p-12 rounded-xl shadow-lg border border-slate-200 text-center space-y-3">
                                <h3 className="text-lg font-bold text-blue-900">Awaiting Patient Intake</h3>
                                <p className="text-sm text-slate-500">
                                    Fill out patient vitals and select presenting symptoms on the left, then run the diagnosis to view ranked clinical results here.
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}