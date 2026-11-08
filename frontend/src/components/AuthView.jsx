import { useState } from 'react';
import { loginAccount, registerAccount } from '../services/api';

const initialForm = { name: '', email: '', password: '', profession: 'Doctor' };

export default function AuthView({ onAuthenticated }) {
    const [mode, setMode] = useState('login');
    const [form, setForm] = useState(initialForm);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const isRegistering = mode === 'register';

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError('');
        try {
            const result = isRegistering
                ? await registerAccount(form)
                : await loginAccount({ email: form.email, password: form.password });
            onAuthenticated(result, isRegistering);
        } catch (requestError) {
            setError(requestError.response?.data?.detail || 'Unable to connect. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const updateField = (event) => {
        setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
    };

    return (
        <main className="min-h-screen bg-slate-100 px-4 py-10 sm:px-6">
            <section className="mx-auto max-w-md overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
                <div className="bg-blue-950 px-7 py-8 text-white">
                    <p className="mb-2 text-sm font-semibold uppercase tracking-widest text-teal-300">PharmAI</p>
                    <h1 className="text-2xl font-bold">Clinical Decision Support</h1>
                    <p className="mt-2 text-sm text-blue-100">Sign in to securely access your clinical workspace.</p>
                </div>

                <div className="p-6 sm:p-8">
                    <div className="mb-6 grid grid-cols-2 rounded-lg bg-slate-100 p-1" role="tablist" aria-label="Account access">
                        <button
                            type="button"
                            role="tab"
                            aria-selected={!isRegistering}
                            onClick={() => { setMode('login'); setError(''); }}
                            className={`rounded-md px-3 py-2 text-sm font-semibold ${!isRegistering ? 'bg-white text-blue-900 shadow-sm' : 'text-slate-600'}`}
                        >
                            Sign in
                        </button>
                        <button
                            type="button"
                            role="tab"
                            aria-selected={isRegistering}
                            onClick={() => { setMode('register'); setError(''); }}
                            className={`rounded-md px-3 py-2 text-sm font-semibold ${isRegistering ? 'bg-white text-blue-900 shadow-sm' : 'text-slate-600'}`}
                        >
                            Create account
                        </button>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {isRegistering && (
                            <>
                                <label className="block text-sm font-medium text-slate-700">
                                    Full name
                                    <input
                                        name="name"
                                        type="text"
                                        autoComplete="name"
                                        required
                                        minLength={2}
                                        maxLength={100}
                                        value={form.name}
                                        onChange={updateField}
                                        className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                                    />
                                </label>
                                <label className="block text-sm font-medium text-slate-700">
                                    Profession
                                    <select
                                        name="profession"
                                        value={form.profession}
                                        onChange={updateField}
                                        className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                                    >
                                        <option>Doctor</option>
                                        <option>Nurse</option>
                                        <option>Health worker</option>
                                    </select>
                                </label>
                            </>
                        )}
                        <label className="block text-sm font-medium text-slate-700">
                            Work email
                            <input
                                name="email"
                                type="email"
                                autoComplete="email"
                                required
                                maxLength={254}
                                value={form.email}
                                onChange={updateField}
                                className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                            />
                        </label>
                        <label className="block text-sm font-medium text-slate-700">
                            Password
                            <input
                                name="password"
                                type="password"
                                autoComplete={isRegistering ? 'new-password' : 'current-password'}
                                required
                                minLength={isRegistering ? 12 : 1}
                                maxLength={128}
                                value={form.password}
                                onChange={updateField}
                                className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                            />
                            {isRegistering && <span className="mt-1 block text-xs text-slate-500">Use at least 12 characters.</span>}
                        </label>

                        {error && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-blue-900 px-4 py-3 font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading ? 'Please wait...' : isRegistering ? 'Create account' : 'Sign in'}
                        </button>
                    </form>

                    <p className="mt-6 text-center text-xs leading-relaxed text-slate-500">
                        For healthcare professionals. PharmAI supports clinical decision-making and does not replace professional judgment.
                    </p>
                    {isRegistering && (
                        <p className="mt-2 text-center text-xs text-slate-500">
                            Profession is self-reported; registration does not verify clinical credentials.
                        </p>
                    )}
                </div>
            </section>
        </main>
    );
}
