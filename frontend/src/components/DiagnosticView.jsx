export default function DiagnosticView({ result }) {
    if (!result) return null;

    const isEmergency = result.emergency_triage_alert !== null || 
        (result.top_predictions && result.top_predictions.length > 0 && result.top_predictions[0].predicted_disease === "EMERGENCY REFERRAL REQUIRED");

    return (
        <div className={`p-4 sm:p-6 lg:p-8 rounded-xl shadow-lg border transition-all ${isEmergency ? 'bg-red-50 border-red-300' : 'bg-white border-slate-200'}`}>
            <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-5">
                <h2 className={`text-xl font-extrabold tracking-tight ${isEmergency ? 'text-red-700' : 'text-blue-900'}`}>
                    {isEmergency ? 'EMERGENCY TRIAGE ALERT' : 'Ranked Clinical Diagnostic Results'}
                </h2>
            </div>

            {isEmergency ? (
                <div className="space-y-3 bg-red-100 border border-red-400 p-5 rounded-lg text-red-800">
                    <p className="font-bold text-base">{result.emergency_triage_alert || (result.top_predictions && result.top_predictions[0]?.description)}</p>
                    <p className="text-sm font-medium">Action required: Immediate medical referral mandated.</p>
                </div>
            ) : (
                <div className="space-y-6">
                    <p className="text-xs text-slate-500">
                        Ranked by the XGBoost model. Model scores are not calibrated probabilities or diagnostic confidence.
                    </p>
                    {result.top_predictions && result.top_predictions.map((pred, index) => {
                        const rawScore = pred.model_score ?? pred.confidence_score;
                        const parsedScore = Number(rawScore);
                        const hasValidScore = rawScore !== null && rawScore !== undefined &&
                            Number.isFinite(parsedScore) && parsedScore >= 0 && parsedScore <= 1;
                        const modelScore = hasValidScore ? `${(parsedScore * 100).toFixed(1)}%` : 'Unavailable';
                        const scoreColor = hasValidScore && parsedScore > 0.7
                            ? 'bg-teal-100 text-teal-800 border-teal-300' 
                            : hasValidScore && parsedScore > 0.4
                            ? 'bg-amber-100 text-amber-800 border-amber-300' 
                            : 'bg-red-100 text-red-800 border-red-300';

                        return (
                            <div key={index} className="min-w-0 p-4 sm:p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-4 shadow-sm">
                                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-200 pb-3">
                                    <div className="flex min-w-0 items-center space-x-3">
                                        <span className="bg-blue-900 text-white text-xs font-bold px-2.5 py-1 rounded-md">
                                            Rank #{index + 1}
                                        </span>
                                        <h3 className="min-w-0 text-lg font-bold text-blue-900 capitalize break-words">{pred.predicted_disease}</h3>
                                    </div>
                                    <span className={`self-start sm:self-auto shrink-0 text-xs font-bold px-3 py-1 rounded-full border ${scoreColor}`}>
                                        Model score: {modelScore}
                                    </span>
                                </div>

                                {pred.matched_symptoms?.length > 0 && (
                                    <p className="text-xs text-slate-600">
                                        Dataset symptoms matching: {pred.matched_symptoms.map(symptom => symptom.replace(/_/g, ' ')).join(', ')}
                                    </p>
                                )}

                                <p className="text-slate-700 text-sm leading-relaxed">{pred.description}</p>

                                {pred.recommended_medicine && pred.dosage_instruction ? (
                                    <div className="bg-teal-50/60 p-4 rounded-lg border border-teal-200 space-y-3">
                                        <h4 className="text-xs font-bold text-teal-800 uppercase tracking-wider">Reviewed Medication Guidance</h4>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <span className="text-xs font-semibold text-slate-500 block">Recommended Medicine:</span>
                                                <p className="font-bold text-slate-800 text-sm">{pred.recommended_medicine}</p>
                                            </div>
                                            <div>
                                                <span className="text-xs font-semibold text-slate-500 block">Dosage:</span>
                                                <p className="text-slate-700 text-xs font-medium">{pred.dosage_instruction}</p>
                                            </div>
                                        </div>
                                        <div className="border-t border-teal-200/60 pt-2 text-xs text-slate-600">
                                            Reviewed by {pred.medication_reviewed_by} on {pred.medication_reviewed_at}. Source: {pred.medication_source}
                                        </div>
                                    </div>
                                ) : null}

                                {pred.common_medications_reference && (
                                    <div className="rounded-lg border border-slate-300 bg-slate-100 p-4">
                                        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                                            Medical reference{pred.medication_category ? ` · ${pred.medication_category}` : ''}
                                        </h4>
                                        <p className="mt-2 text-sm text-slate-800">{pred.common_medications_reference}</p>
                                    </div>
                                )}

                                {/* Pregnancy Safety Warning Box */}
                                {pred.pregnancy_warnings && pred.pregnancy_warnings.length > 0 && (
                                    <div className="bg-amber-50 border-l-4 border-amber-500 p-3 rounded-r-lg shadow-sm">
                                        <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wider">Pregnancy Safety Screening Warning</h4>
                                        <ul className="mt-1 text-xs text-amber-800 space-y-1 list-disc list-inside">
                                            {pred.pregnancy_warnings.map((warn, wIndex) => (
                                                <li key={wIndex}>{warn}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {/* Precautions List */}
                                {pred.precautions && pred.precautions.length > 0 && (
                                    <div>
                                        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1.5">Clinical Precautions:</span>
                                        <ul className="space-y-1 bg-white p-3 rounded-lg border border-slate-200">
                                            {pred.precautions.map((p, pIndex) => (
                                                <li key={pIndex} className="text-xs text-slate-700 flex items-start space-x-2">
                                                    <span className="text-teal-600 font-bold">•</span>
                                                    <span>{p}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}