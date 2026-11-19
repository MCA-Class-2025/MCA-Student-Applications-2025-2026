function AssessmentResult({ result, error, guidance, guidanceError, guidanceStatus, onGetGuidance }) {
  return (
    <aside className="space-y-5">
      {result ? (
        <section className="overflow-hidden rounded-3xl border border-teal/20 bg-white shadow-sm">
          <div className="bg-mint p-6">
            <p className="text-sm font-semibold text-teal">Your prediction</p>
            <h2 className="mt-2 text-3xl font-bold text-navy">{result.risk_label}</h2>
            <div className="mt-5 rounded-2xl bg-white/80 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Estimated model probability</p>
              <p className="mt-1 text-3xl font-bold text-teal">{(result.risk_probability * 100).toFixed(1)}%</p>
            </div>
          </div>
          <div className="p-6">
            {/* <p className="text-sm leading-6 text-slate-600">This estimate supports, but does not replace, advice from a qualified healthcare professional.</p> */}
            <button type="button" onClick={onGetGuidance} disabled={guidanceStatus === 'loading'} className="mt-5 w-full rounded-xl bg-navy px-4 py-3 text-sm font-semibold text-white transition hover:bg-navy/90 disabled:cursor-not-allowed disabled:opacity-60">
              {guidanceStatus === 'loading' ? 'Creating guidance...' : 'Get wellness guidance'}
            </button>
          </div>
        </section>
      ) : (
        <section className="rounded-3xl border border-dashed border-slate-300 bg-white/60 p-7 text-center">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-slate-100 text-xl text-slate-400" aria-hidden="true">♡</span>
          <h2 className="mt-4 font-bold text-navy">Your result will appear here</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">Complete the health snapshot to receive your result.</p>
        </section>
      )}
      {guidance && <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><p className="text-sm font-semibold text-teal">Wellness guidance</p><p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-700">{guidance.recommendation}</p></section>}
      {guidanceError && <p role="alert" className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">{guidanceError}</p>}
      {error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-800">{error}</p>}
    </aside>
  )
}

export default AssessmentResult
