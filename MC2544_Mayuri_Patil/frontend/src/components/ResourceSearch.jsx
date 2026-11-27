import { useState } from 'react'

function ResourceSearch({ type, eyebrow, title, description, placeholder, search }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setStatus('loading')
    setError('')
    try {
      setResults(await search(query))
      setStatus('complete')
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to complete this search. Please try again later.')
      setStatus('error')
    }
  }

  return (
    <section className="flex flex-col rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-teal">{eyebrow}</p>
      <h3 className="mt-2 text-xl font-bold text-navy">{title}</h3>
      <p className="mt-2 min-h-12 text-sm leading-6 text-slate-600">{description}</p>
      <form onSubmit={handleSubmit} className="mt-5 flex gap-2">
        <input required minLength="2" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={placeholder} aria-label={`Search ${title.toLowerCase()}`} className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-teal focus:bg-white focus:ring-4 focus:ring-teal/10" />
        <button disabled={status === 'loading'} className="rounded-xl bg-teal px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-teal/90 disabled:opacity-60">{status === 'loading' ? '...' : 'Search'}</button>
      </form>
      {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{error}</p>}
      {status === 'complete' && results.length === 0 && <p className="mt-4 text-sm text-slate-500">No matches found.</p>}
      {results.length > 0 && <div className="mt-5 space-y-3">{results.map((item, index) => <ResultCard key={`${item.name ?? item.brand_name}-${index}`} item={item} type={type} />)}</div>}
    </section>
  )
}

function ResultCard({ item, type }) {
  if (type === 'drug') {
    return <article className="rounded-2xl bg-slate-50 p-4"><h4 className="font-semibold text-navy">{item.brand_name ?? item.generic_name ?? 'Unnamed drug'}</h4>{item.generic_name && item.generic_name !== item.brand_name && <p className="mt-1 text-xs text-slate-500">Generic: {item.generic_name}</p>}{item.purpose && <p className="mt-3 text-sm leading-5 text-slate-700"><strong>Purpose:</strong> {item.purpose}</p>}{item.warnings && <p className="mt-2 text-sm leading-5 text-slate-700"><strong>Warnings:</strong> {item.warnings}</p>}</article>
  }

  return <article className="rounded-2xl bg-slate-50 p-4"><h4 className="font-semibold text-navy">{item.name ?? 'Unnamed food'}</h4>{item.brand && <p className="mt-1 text-xs text-slate-500">{item.brand}</p>}{type === 'packaged' && item.nutrition_grade && <p className="mt-3 text-sm text-slate-700">Nutri-Score: <strong className="uppercase">{item.nutrition_grade}</strong></p>}<p className="mt-2 text-sm text-slate-700">Calories: <strong>{item.calories ?? 'Not available'}{item.calories !== null && item.calories !== undefined ? ' kcal' : ''}</strong></p>{type === 'packaged' && <p className="mt-1 text-sm text-slate-700">Sodium: <strong>{item.sodium ?? 'Not available'}{item.sodium !== null && item.sodium !== undefined ? ' g' : ''}</strong></p>}</article>
}

export default ResourceSearch
