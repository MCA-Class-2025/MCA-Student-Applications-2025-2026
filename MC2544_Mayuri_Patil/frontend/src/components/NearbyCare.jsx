import { useState } from 'react'

function NearbyCare({ findNearbyCare }) {
  const [care, setCare] = useState([])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  function handleFindCare() {
    if (!navigator.geolocation) {
      setError('Location services are not supported by this browser.')
      setStatus('error')
      return
    }

    setStatus('loading')
    setError('')
    navigator.geolocation.getCurrentPosition(async (position) => {
      try {
        setCare(await findNearbyCare(position.coords.latitude, position.coords.longitude))
        setStatus('complete')
      } catch (requestError) {
        setError(requestError.response?.data?.detail || 'Unable to find nearby care. Please try again later.')
        setStatus('error')
      }
    }, () => {
      setError('Location access is needed to find nearby care.')
      setStatus('error')
    })
  }

  return (
    <section className="mt-12 rounded-3xl bg-teal p-6 text-white shadow-lg shadow-teal/15 sm:p-8">
      <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
        <div className="max-w-2xl"><p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal-100">Nearby care</p><h2 className="mt-2 text-3xl font-bold">Find support near you.</h2><p className="mt-2 leading-7 text-teal-50">Use your location to see nearby hospitals and healthcare services.</p></div>
        <button type="button" onClick={handleFindCare} disabled={status === 'loading'} className="shrink-0 rounded-xl bg-white px-5 py-3 font-semibold text-teal transition hover:bg-teal-50 disabled:cursor-not-allowed disabled:opacity-60">{status === 'loading' ? 'Finding care...' : 'Find nearby care'}</button>
      </div>
      {error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}
      {status === 'complete' && care.length === 0 && <p className="mt-5 text-sm text-teal-50">No nearby healthcare services were found.</p>}
      {care.length > 0 && <div className="mt-6 grid gap-4 md:grid-cols-2 lg:grid-cols-3">{care.map((service, index) => <article className="rounded-2xl bg-white p-5 text-slate-700" key={`${service.name}-${index}`}><h3 className="font-semibold text-navy">{service.name}</h3>{service.type && <p className="mt-2 text-sm capitalize text-teal">{service.type}</p>}{service.address && <p className="mt-3 text-sm">{service.address}</p>}</article>)}</div>}
    </section>
  )
}

export default NearbyCare
