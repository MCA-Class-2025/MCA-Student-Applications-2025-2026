import { useState } from 'react'

const sampleQuestions = [
  'What LOINC code identifies serum creatinine?',
  'What unit is used for serum creatinine?',
  'How many patient-laboratory records are in the fused dataset?',
]

function Phase2Rag({ askPhase2Question }) {
  const [question, setQuestion] = useState('')
  const [state, setState] = useState({ status: 'idle', result: null, error: '' })

  async function handleSubmit(event) {
    event.preventDefault()
    setState({ status: 'loading', result: null, error: '' })

    try {
      const result = await askPhase2Question(question)
      setState({ status: 'complete', result, error: '' })
    } catch (requestError) {
      setState({
        status: 'error',
        result: null,
        error: requestError.response?.data?.detail || 'Unable to answer this question. Please try again later.',
      })
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-7">
      <section className="rounded-3xl bg-navy p-7 text-white shadow-xl shadow-slate-300/50 sm:p-9">
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-200">Phase 2 RAG assistant</p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight sm:text-4xl">Ask questions about the fused heart-failure dataset.</h2>
        <p className="mt-4 max-w-3xl leading-7 text-slate-300">Answers are grounded in the original dataset and NLM LOINC-enriched records. Each response shows the source records retrieved for the answer.</p>

        <form onSubmit={handleSubmit} className="mt-7">
          <label className="sr-only" htmlFor="phase2-question">Question about the fused dataset</label>
          <div className="flex flex-col gap-3 sm:flex-row">
            <input
              id="phase2-question"
              required
              minLength="5"
              maxLength="500"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="e.g. What LOINC code identifies serum creatinine?"
              className="min-w-0 flex-1 rounded-xl border border-white/20 bg-white px-4 py-3 text-slate-900 outline-none placeholder:text-slate-400 focus:ring-4 focus:ring-teal/30"
            />
            <button disabled={state.status === 'loading'} className="rounded-xl bg-teal px-5 py-3 font-semibold text-white transition hover:bg-teal/90 disabled:cursor-not-allowed disabled:opacity-60">
              {state.status === 'loading' ? 'Searching records...' : 'Ask assistant'}
            </button>
          </div>
        </form>

        <div className="mt-5 flex flex-wrap gap-2">
          {sampleQuestions.map((sampleQuestion) => (
            <button key={sampleQuestion} type="button" onClick={() => setQuestion(sampleQuestion)} className="rounded-full border border-white/20 px-3 py-1.5 text-left text-xs font-medium text-slate-200 transition hover:bg-white/10">
              {sampleQuestion}
            </button>
          ))}
        </div>
      </section>

      {state.error && <p role="alert" className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-800">{state.error}</p>}

      {state.result && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_280px]">
          <section className="rounded-3xl border border-teal/20 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-teal">Grounded answer</p>
            <p className="mt-3 whitespace-pre-line text-base leading-7 text-slate-700">{state.result.answer}</p>
          </section>

          <aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <p className="text-sm font-semibold text-navy">Retrieved sources</p>
            <p className="mt-2 text-xs leading-5 text-slate-500">These records were supplied to the language model as its answer context.</p>
            <ol className="mt-4 space-y-3">
              {state.result.sources.map((source) => (
                <li key={`${source.source}-${source.record_id}`} className="rounded-xl bg-mint/50 p-3">
                  <p className="break-words font-mono text-xs font-semibold text-teal">{source.source}</p>
                  <p className="mt-1 break-words text-xs text-slate-600">Record: {source.record_id}</p>
                  <p className="mt-1 text-xs text-slate-500">Relevance: {(source.score * 100).toFixed(1)}%</p>
                </li>
              ))}
            </ol>
          </aside>
        </div>
      )}
    </div>
  )
}

export default Phase2Rag
