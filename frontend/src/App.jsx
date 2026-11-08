import { useEffect, useState } from 'react';
import IntakeForm from './components/IntakeForm';
import DiagnosticView from './components/DiagnosticView';
import AuthView from './components/AuthView';
import ProfileEditor from './components/ProfileEditor';
import {
    clearAccessToken,
    fetchCurrentAccount,
    saveAccessToken,
    submitPatientIntake,
} from './services/api';

export default function App() {
    const [user, setUser] = useState(null);
    const [checkingSession, setCheckingSession] = useState(
        Boolean(localStorage.getItem('pharmai_access_token'))
    );
    const [diagnosticResult, setDiagnosticResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [diagnosisError, setDiagnosisError] = useState('');
    const [authSuccessMessage, setAuthSuccessMessage] = useState('');
    const [profileEditorOpen, setProfileEditorOpen] = useState(false);

    useEffect(() => {
        const handleSessionExpired = () => {
            setUser(null);
            setDiagnosticResult(null);
            setDiagnosisError('');
            setAuthSuccessMessage('');
            setProfileEditorOpen(false);
        };
        window.addEventListener('pharmai:session-expired', handleSessionExpired);

        if (localStorage.getItem('pharmai_access_token')) {
            fetchCurrentAccount()
                .then(setUser)
                .catch(() => clearAccessToken())
                .finally(() => setCheckingSession(false));
        }

        return () => window.removeEventListener('pharmai:session-expired', handleSessionExpired);
    }, []);

    const handleAuthenticated = (result, isRegistration) => {
        saveAccessToken(result.access_token);
        setUser(result.user);
        setAuthSuccessMessage(
            isRegistration
                ? `Your account was created successfully. Welcome, ${result.user.name}!`
                : `You signed in successfully. Welcome back, ${result.user.name}!`
        );
    };

    const handleSignOut = () => {
        clearAccessToken();
        setUser(null);
        setDiagnosticResult(null);
        setDiagnosisError('');
        setAuthSuccessMessage('');
        setProfileEditorOpen(false);
    };

    const handleProfileUpdated = (updatedUser) => {
        setUser(updatedUser);
        setProfileEditorOpen(false);
        setAuthSuccessMessage('Your profile was updated successfully.');
    };

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

    if (checkingSession) {
        return <main className="flex min-h-screen items-center justify-center text-sm font-medium text-slate-600">Checking your session...</main>;
    }

    if (!user) {
        return <AuthView onAuthenticated={handleAuthenticated} />;
    }

    return (
        <div className="min-h-screen bg-slate-100 text-slate-900">
            <header className="bg-blue-900 text-white py-4 px-4 sm:px-6 lg:px-8 shadow-md">
                <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
                    <h1 className="text-base sm:text-xl font-extrabold tracking-tight">PharmAI Clinical Decision Support</h1>
                    <div className="flex items-center gap-3">
                        <span className="hidden text-right text-xs sm:block">
                            <span className="block font-semibold">{user.name}</span>
                            <span className="text-blue-200">{user.profession}</span>
                        </span>
                        <button
                            type="button"
                            onClick={() => setProfileEditorOpen(true)}
                            className="shrink-0 rounded-full border border-blue-300 px-3 py-1.5 text-xs font-semibold hover:bg-blue-800"
                        >
                            Edit profile
                        </button>
                        <button
                            type="button"
                            onClick={handleSignOut}
                            className="shrink-0 rounded-full bg-teal-600 px-3 py-1.5 text-xs font-semibold hover:bg-teal-500"
                        >
                            Sign out
                        </button>
                    </div>
                </div>
            </header>

            {profileEditorOpen && (
                <ProfileEditor
                    user={user}
                    onClose={() => setProfileEditorOpen(false)}
                    onUpdated={handleProfileUpdated}
                />
            )}

            <main className="w-full max-w-7xl mx-auto p-4 sm:p-6">
                {authSuccessMessage && (
                    <div
                        role="status"
                        aria-live="polite"
                        className="mb-5 flex items-center justify-between gap-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800"
                    >
                        <span>{authSuccessMessage}</span>
                        <button
                            type="button"
                            onClick={() => setAuthSuccessMessage('')}
                            aria-label="Dismiss success message"
                            className="shrink-0 rounded px-2 py-1 text-emerald-800 hover:bg-emerald-100"
                        >
                            Dismiss
                        </button>
                    </div>
                )}
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