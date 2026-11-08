import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL
    || (import.meta.env.DEV ? 'http://127.0.0.1:8000' : 'https://pharmai-7q9h.onrender.com');
// const API_BASE_URL = '';
// const API_BASE_URL = 'http://localhost:8000';
// const API_BASE_URL = '/api';

const api = axios.create({ baseURL: API_BASE_URL });

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('pharmai_access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401 && !error.config?.url?.endsWith('/auth/login')) {
            clearAccessToken();
            window.dispatchEvent(new Event('pharmai:session-expired'));
        }
        return Promise.reject(error);
    }
);

export const registerAccount = async (accountData) => {
    const response = await api.post('/auth/register', accountData);
    return response.data;
};

export const loginAccount = async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    return response.data;
};

export const fetchCurrentAccount = async () => {
    const response = await api.get('/auth/me');
    return response.data.user;
};

export const updateAccountProfile = async (profile) => {
    const response = await api.patch('/auth/me', profile);
    return response.data.user;
};

export const saveAccessToken = (token) => {
    localStorage.setItem('pharmai_access_token', token);
};

export const clearAccessToken = () => {
    localStorage.removeItem('pharmai_access_token');
};

export const submitPatientIntake = async (intakeData) => {
    try {
        const response = await api.post('/predict', intakeData);
        return response.data;
    } catch (error) {
        console.error('Error submitting patient intake:', error);
        throw error;
    }
};

export const fetchTreatmentSummary = async (disease, weightKg, age) => {
    try {
        const response = await api.get('/treatment-summary', {
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
        const response = await api.get('/symptoms/all');
        return response.data.symptoms;
    } catch (error) {
        console.error('Error fetching symptoms:', error);
        throw error;
    }
};