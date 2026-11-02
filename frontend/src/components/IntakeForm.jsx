import { useState, useEffect } from 'react';
import { fetchSymptoms } from '../services/api';

const formatSymptomName = (name) => {
    if (!name) return '';
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (char) => char.toUpperCase());
};

export default function IntakeForm({ onSubmit, loading }) {
    const [formData, setFormData] = useState({
        age: 25,
        gender: 'Female',
        weight_kg: 70.0,
        temperature: 37.2,
        symptom_duration_days: 3,
        is_pregnant: false,
        symptoms: []
    });

    const [availableSymptoms, setAvailableSymptoms] = useState([]);
    const [fetchingSymptoms, setFetchingSymptoms] = useState(true);

    useEffect(() => {
        const loadSymptoms = async () => {
            try {
                const data = await fetchSymptoms();
                setAvailableSymptoms(data.symptoms || data || []);
            } catch (error) {
                console.error('Failed to load symptoms list from backend', error);
            } finally {
                setFetchingSymptoms(false);
            }
        };

        loadSymptoms();
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData({
            ...formData,
            [name]: type === 'checkbox' ? checked : value
        });
    };

    const handleSelectSymptomChange = (e) => {
        const symptom = e.target.value;
        if (!symptom || formData.symptoms.includes(symptom)) return;
        
        setFormData({
            ...formData,
            symptoms: [...formData.symptoms, symptom]
        });
    };

    const handleRemoveSymptom = (symptom) => {
        setFormData({
            ...formData,
            symptoms: formData.symptoms.filter(s => s !== symptom)
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        const payload = {
            ...formData,
            age: parseInt(formData.age, 10),
            weight_kg: parseFloat(formData.weight_kg),
            temperature: formData.temperature ? parseFloat(formData.temperature) : null,
            symptom_duration_days: parseInt(formData.symptom_duration_days, 10),
            allergies: [],
            chronic_conditions: [],
            symptoms: formData.symptoms
        };
        onSubmit(payload);
    };

    return (
        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-lg border border-slate-200 space-y-6">
            <div className="border-b border-slate-200 pb-4">
                <h2 className="text-2xl font-extrabold text-blue-900 tracking-tight">Patient Clinical Intake</h2>
                <p className="text-xs text-slate-500 mt-1">Enter patient vitals and select presenting symptoms for evaluation.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">Age (Years)</label>
                    <input 
                        type="number" 
                        name="age" 
                        value={formData.age} 
                        onChange={handleChange} 
                        className="w-full border border-slate-300 rounded-lg p-2.5 text-slate-800 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-600 focus:border-teal-600 outline-none transition" 
                        required 
                    />
                </div>
                <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">Biological Sex</label>
                    <select 
                        name="gender" 
                        value={formData.gender} 
                        onChange={handleChange} 
                        className="w-full border border-slate-300 rounded-lg p-2.5 text-slate-800 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-600 focus:border-teal-600 outline-none transition"
                    >
                        <option value="Female">Female</option>
                        <option value="Male">Male</option>
                    </select>
                </div>
                <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">Weight (kg)</label>
                    <input 
                        type="number" 
                        step="0.1" 
                        name="weight_kg" 
                        value={formData.weight_kg} 
                        onChange={handleChange} 
                        className="w-full border border-slate-300 rounded-lg p-2.5 text-slate-800 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-600 focus:border-teal-600 outline-none transition" 
                        required 
                    />
                </div>
                <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">Body Temp (°C)</label>
                    <input 
                        type="number" 
                        step="0.1" 
                        name="temperature" 
                        value={formData.temperature} 
                        onChange={handleChange} 
                        className="w-full border border-slate-300 rounded-lg p-2.5 text-slate-800 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-600 focus:border-teal-600 outline-none transition" 
                    />
                </div>
                <div>
                    <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-1">Duration (Days)</label>
                    <input 
                        type="number" 
                        name="symptom_duration_days" 
                        value={formData.symptom_duration_days} 
                        onChange={handleChange} 
                        className="w-full border border-slate-300 rounded-lg p-2.5 text-slate-800 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-teal-600 focus:border-teal-600 outline-none transition" 
                        required 
                    />
                </div>
                {formData.gender === 'Female' && (
                    <div className="flex items-center pt-6">
                        <label className="inline-flex items-center cursor-pointer space-x-2">
                            <input 
                                type="checkbox" 
                                name="is_pregnant" 
                                checked={formData.is_pregnant} 
                                onChange={handleChange} 
                                className="h-5 w-5 text-teal-600 border-slate-300 rounded focus:ring-teal-500 accent-teal-600" 
                            />
                            <span className="text-sm font-semibold text-slate-700">Patient is Pregnant</span>
                        </label>
                    </div>
                )}
            </div>

            <div className="space-y-4 border-t border-slate-200 pt-5">
                <div className="flex items-center justify-between">
                    <label className="text-sm font-bold text-blue-900 uppercase tracking-wider">Presenting Symptoms</label>
                    <span className="text-xs font-semibold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-full border border-teal-200">
                        {formData.symptoms.length} Selected
                    </span>
                </div>
                
                <div>
                    <select
                        value=""
                        onChange={handleSelectSymptomChange}
                        disabled={fetchingSymptoms}
                        className="w-full p-3 border border-slate-300 rounded-lg text-sm text-slate-800 bg-white focus:ring-2 focus:ring-teal-600 focus:border-teal-600 outline-none shadow-sm transition"
                    >
                        <option value="" disabled>
                            {fetchingSymptoms ? 'Loading symptoms...' : '-- Click to add a symptom from database --'}
                        </option>
                        {Array.isArray(availableSymptoms) && availableSymptoms
                            .filter(s => !formData.symptoms.includes(s))
                            .map((symptom) => (
                                <option key={symptom} value={symptom}>
                                    {formatSymptomName(symptom)}
                                </option>
                            ))}
                    </select>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200">
                    <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-2">Active Selection Tray:</span>
                    <div className="flex flex-wrap gap-2 min-h-[36px]">
                        {formData.symptoms.length === 0 ? (
                            <span className="text-sm text-slate-400 italic">No symptoms selected. Choose from the dropdown menu above.</span>
                        ) : (
                            formData.symptoms.map((symptom) => (
                                <span 
                                    key={symptom} 
                                    className="bg-blue-900 text-white text-xs font-semibold px-3 py-1.5 rounded-full flex items-center space-x-1.5 shadow-sm transition"
                                >
                                    <span>{formatSymptomName(symptom)}</span>
                                    <button 
                                        type="button" 
                                        onClick={() => handleRemoveSymptom(symptom)} 
                                        className="ml-1 text-slate-300 hover:text-red-300 font-bold focus:outline-none"
                                        title="Remove symptom"
                                    >
                                        ✕
                                    </button>
                                </span>
                            ))
                        )}
                    </div>
                </div>
            </div>

            <button 
                type="submit" 
                disabled={loading || formData.symptoms.length === 0} 
                className="w-full bg-blue-900 hover:bg-blue-800 text-white font-bold py-3 px-4 rounded-lg shadow-md hover:shadow-lg disabled:bg-slate-300 disabled:cursor-not-allowed transition duration-200"
            >
                {loading ? 'Evaluating Diagnosis...' : 'Run Clinical Diagnosis'}
            </button>
        </form>
    );
}