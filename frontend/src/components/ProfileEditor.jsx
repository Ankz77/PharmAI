import { useState } from 'react';
import { updateAccountProfile } from '../services/api';

export default function ProfileEditor({ user, onClose, onUpdated }) {
    const [name, setName] = useState(user.name);
    const [profession, setProfession] = useState(user.profession);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (event) => {
        event.preventDefault();
        setLoading(true);
        setError('');
        try {
            const updatedUser = await updateAccountProfile({ name, profession });
            onUpdated(updatedUser);
        } catch (requestError) {
            setError(requestError.response?.data?.detail || 'Unable to update your profile. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget && !loading) onClose();
            }}
        >
            <section
                role="dialog"
                aria-modal="true"
                aria-labelledby="profile-editor-title"
                className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl sm:p-8"
            >
                <h2 id="profile-editor-title" className="text-xl font-bold text-blue-950">Edit your profile</h2>
                <p className="mt-1 text-sm text-slate-500">Update the name and profession shown in your workspace.</p>

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                    <label className="block text-sm font-medium text-slate-700">
                        Full name
                        <input
                            type="text"
                            autoComplete="name"
                            required
                            minLength={2}
                            maxLength={100}
                            value={name}
                            onChange={(event) => setName(event.target.value)}
                            className="mt-1.5 w-full rounded-lg border border-slate-300 px-3 py-2.5 text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                        />
                    </label>

                    <label className="block text-sm font-medium text-slate-700">
                        Profession
                        <select
                            value={profession}
                            onChange={(event) => setProfession(event.target.value)}
                            className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 outline-none focus:border-blue-700 focus:ring-2 focus:ring-blue-100"
                        >
                            <option>Doctor</option>
                            <option>Nurse</option>
                            <option>Health worker</option>
                        </select>
                    </label>

                    <p className="text-sm text-slate-500">
                        Email: <span className="font-medium text-slate-700">{user.email}</span>
                    </p>

                    {error && <p role="alert" className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}

                    <div className="flex justify-end gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={loading}
                            className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="rounded-lg bg-blue-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading ? 'Saving...' : 'Save changes'}
                        </button>
                    </div>
                </form>
            </section>
        </div>
    );
}
