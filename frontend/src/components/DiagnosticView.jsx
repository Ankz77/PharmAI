export default function DiagnosticView({ result }) {
    if (!result) return null;

    const isEmergency = result.emergency_triage_alert !== null || 
        (result.top_predictions && result.top_predictions.length > 0 && result.top_predictions[0].predicted_disease === "EMERGENCY REFERRAL REQUIRED");

    return (
        <div className={`mt-6 p-8 rounded-xl shadow-lg border transition-all ${isEmergency ? 'bg-red-50 border-red-300' : 'bg-white border-slate-200'}`}>
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
                    {result.top_predictions && result.top_predictions.map((pred, index) => {
                        const confidencePercent = (pred.confidence_score * 100).toFixed(1);
                        const confidenceColor = pred.confidence_score > 0.7 
                            ? 'bg-teal-100 text-teal-800 border-teal-300' 
                            : pred.confidence_score > 0.4 
                            ? 'bg-amber-100 text-amber-800 border-amber-300' 
                            : 'bg-red-100 text-red-800 border-red-300';

                        return (
                            <div key={index} className="p-6 rounded-xl border border-slate-200 bg-slate-50/50 space-y-4 shadow-sm">
                                <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                                    <div className="flex items-center space-x-3">
                                        <span className="bg-blue-900 text-white text-xs font-bold px-2.5 py-1 rounded-md">
                                            Rank #{index + 1}
                                        </span>
                                        <h3 className="text-lg font-bold text-blue-900 capitalize">{pred.predicted_disease}</h3>
                                    </div>
                                    <span className={`text-xs font-bold px-3 py-1 rounded-full border ${confidenceColor}`}>
                                        Confidence: {confidencePercent}%
                                    </span>
                                </div>

                                <p className="text-slate-700 text-sm leading-relaxed">{pred.description}</p>

                                {/* Medication & Physical Breakdown Container */}
                                <div className="bg-teal-50/60 p-4 rounded-lg border border-teal-200 space-y-3">
                                    <h4 className="text-xs font-bold text-teal-800 uppercase tracking-wider">Treatment & Dosage Guidance</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        <div>
                                            <span className="text-xs font-semibold text-slate-500 block">Recommended Medicine:</span>
                                            <p className="font-bold text-slate-800 text-sm">{pred.recommended_medicine}</p>
                                        </div>
                                        <div>
                                            <span className="text-xs font-semibold text-slate-500 block">Standard Dosage:</span>
                                            <p className="text-slate-700 text-xs font-medium">{pred.dosage_instruction}</p>
                                        </div>
                                    </div>
                                    <div className="border-t border-teal-200/60 pt-2">
                                        <span className="text-xs font-semibold text-slate-500 block">Physical Unit Breakdown:</span>
                                        <p className="font-semibold text-teal-900 text-xs mt-0.5">{pred.physical_unit_breakdown}</p>
                                    </div>
                                </div>

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