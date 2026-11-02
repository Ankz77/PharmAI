import React, { useState, useEffect } from 'react';
import { fetchSymptoms } from '../services/api';

const SymptomSelector = () => {
    const [symptoms, setSymptoms] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const loadSymptoms = async () => {
            try {
                const data = await fetchSymptoms();
                setSymptoms(data);
            } catch (error) {
                console.error('Failed to load symptoms list');
            } finally {
                setLoading(false);
            }
        };

        loadSymptoms();
    }, []);

    if (loading) return <div>Loading symptoms...</div>;

    return (
        <div>
            <h3>Select Symptoms</h3>
            {/* Render your symptom checkboxes or dropdown here using the 'symptoms' array */}
        </div>
    );
};

export default SymptomSelector;