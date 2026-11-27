const fields = [
  { name: 'patient_id', label: 'Patient ID', type: 'text', maxLength: 64, pattern: '[A-Za-z0-9_-]+', placeholder: 'e.g. patient_001' },
  { name: 'age', label: 'Age (years)', min: 18, max: 120, placeholder: 'e.g. 54' },
  { name: 'gender', label: 'Gender', type: 'select', options: [['1', 'Female'], ['2', 'Male']] },
  { name: 'height', label: 'Height (cm)', min: 120, max: 220, placeholder: 'e.g. 168' },
  { name: 'weight', label: 'Weight (kg)', min: 30, max: 250, step: 0.1, placeholder: 'e.g. 70' },
  { name: 'ap_hi', label: 'Systolic pressure', min: 70, max: 250, placeholder: 'e.g. 120' },
  { name: 'ap_lo', label: 'Diastolic pressure', min: 40, max: 200, placeholder: 'e.g. 80' },
  { name: 'cholesterol', label: 'Cholesterol level', type: 'select', options: [['1', 'Normal'], ['2', 'Above normal'], ['3', 'Well above normal']] },
  { name: 'gluc', label: 'Glucose level', type: 'select', options: [['1', 'Normal'], ['2', 'Above normal'], ['3', 'Well above normal']] },
  { name: 'smoke', label: 'Smoker', type: 'select', options: [['0', 'No'], ['1', 'Yes']] },
  { name: 'alco', label: 'Alcohol intake', type: 'select', options: [['0', 'No'], ['1', 'Yes']] },
  { name: 'active', label: 'Physically active', type: 'select', options: [['1', 'Yes'], ['0', 'No']] },
]

function AssessmentForm({ values, onValueChange, onSubmit, status }) {
  return (
    <form onSubmit={onSubmit} className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
      <div className="mb-8 flex items-start gap-4">
        <span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-mint text-xl text-teal" aria-hidden="true">♥</span>
        <div>
          <p className="text-sm font-semibold text-teal">Risk assessment</p>
          <h2 className="mt-1 text-2xl font-bold text-navy">Your health snapshot</h2>
          <p className="mt-1 text-sm text-slate-500">All fields are required for an accurate estimate.</p>
        </div>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        {fields.map((field) => (
          <label className="text-sm font-medium text-slate-700" key={field.name}>
            {field.label}
            {field.type === 'select' ? (
              <select required value={values[field.name] ?? ''} onChange={(event) => onValueChange(field.name, event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 outline-none transition focus:border-teal focus:bg-white focus:ring-4 focus:ring-teal/10">
                <option value="" disabled>Select an option</option>
                {field.options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            ) : (
              <input required type={field.type ?? 'number'} min={field.min} max={field.max} maxLength={field.maxLength} pattern={field.pattern} step={field.step ?? 1} placeholder={field.placeholder} value={values[field.name] ?? ''} onChange={(event) => onValueChange(field.name, event.target.value)} className="mt-2 block w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-teal focus:bg-white focus:ring-4 focus:ring-teal/10" />
            )}
          </label>
        ))}
      </div>
      <button disabled={status === 'loading'} className="mt-8 inline-flex items-center justify-center rounded-xl bg-teal px-5 py-3 font-semibold text-white transition hover:bg-teal/90 focus:outline-none focus:ring-4 focus:ring-teal/20 disabled:cursor-not-allowed disabled:opacity-60">
        {status === 'loading' ? 'Calculating risk...' : 'Calculate my risk'}
      </button>
    </form>
  )
}

export default AssessmentForm
