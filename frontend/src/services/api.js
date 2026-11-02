import axios from 'axios';

// const API_BASE_URL = '';
const API_BASE_URL = 'http://localhost:8000';
// const API_BASE_URL = '/api';

export const submitPatientIntake = async (intakeData) => {
    try {
        const response = await axios.post(`${API_BASE_URL}/predict`, intakeData);
        return response.data;
    } catch (error) {
        console.error('Error submitting patient intake:', error);
        throw error;
    }
};

export const fetchTreatmentSummary = async (disease, weightKg, age) => {
    try {
        const response = await axios.get(`${API_BASE_URL}/treatment-summary`, {
            params: { disease, weight_kg: weightKg, age }
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching treatment summary:', error);
        throw error;
    }
};

export const fetchSymptoms = async () => {
    try {
        const response = await axios.get(`${API_BASE_URL}/symptoms/all`);
        return response.data.symptoms;
    } catch (error) {
        console.error('Error fetching symptoms:', error);
        throw error;
    }
};