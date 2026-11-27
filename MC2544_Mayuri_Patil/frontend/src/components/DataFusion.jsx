import { useState } from 'react'
import { getDatasetPreview, getPhase1DatasetPreview } from '../services/api'

const rawInputs = [
  { title: 'Profile', items: ['Patient ID', 'Age', 'Gender', 'Height', 'Weight'] },
  { title: 'Blood pressure', items: ['Systolic pressure', 'Diastolic pressure'] },
  { title: 'Health factors', items: ['Cholesterol', 'Glucose', 'Smoking', 'Alcohol use', 'Physical activity'] },
]

const fusedSignals = [
  {
    name: 'Body mass index (BMI)',
    formula: 'weight ÷ height²',
    description: 'Combines height and weight into a measure of body size.',
  },
  {
    name: 'Pulse pressure',
    formula: 'systolic pressure − diastolic pressure',
    description: 'Captures the gap between the two blood-pressure readings.',
  },
  {
    name: 'Mean arterial pressure',
    formula: 'diastolic pressure + (pulse pressure ÷ 3)',
    description: 'Estimates the average pressure in the arteries during a heartbeat.',
  },
]

const externalDatasets = [
  {
    id: 'fused_assessments',
    filename: 'fused_assessments.csv',
    source: 'Fused assessment records',
    description: 'Saved assessment inputs, calculated fusion signals, and risk estimates.',
  },
  {
    id: 'huggingface',
    filename: 'huggingface_recommendations.csv',
    source: 'Hugging Face recommendations',
    description: 'Saved AI wellness recommendation requests and responses.',
  },
  {
    id: 'openfda',
    filename: 'openfda_drug_labels.csv',
    source: 'OpenFDA drug labels',
    description: 'Saved medication-label searches and returned reference data.',
  },
  {
    id: 'openfoodfacts',
    filename: 'openfoodfacts_packaged_foods.csv',
    source: 'Open Food Facts',
    description: 'Saved packaged-food nutrition searches and results.',
  },
  {
    id: 'openstreetmap',
    filename: 'openstreetmap_nearby_care.csv',
    source: 'OpenStreetMap nearby care',
    description: 'Saved nearby-care searches and returned locations.',
  },
  {
    id: 'usda',
    filename: 'usda_foods.csv',
    source: 'USDA FoodData Central',
    description: 'Saved food nutrition searches and returned food data.',
  },
]

const phase1Datasets = [
  {
    id: 'original',
    filename: 'heart_failure_clinical_records_dataset.csv',
    source: 'Original dataset',
    description: '299 heart-failure clinical records used as the original Phase 1 dataset.',
  },
  {
    id: 'api',
    filename: 'phase1_api_loinc_metadata.csv',
    source: 'API dataset',
    description: 'NLM Clinical Tables LOINC metadata for serum creatinine and serum sodium.',
  },
  {
    id: 'fused',
    filename: 'phase1_fused_heart_failure_loinc.csv',
    source: 'Fused dataset',
    description: 'Patient laboratory records enriched with LOINC code, display name, unit, and provider.',
  },
]

function DataFusion() {
  const [datasetState, setDatasetState] = useState({ status: 'idle', selectedId: '', selectedDataset: null, data: null, error: '' })

  async function showDataset(dataset, isPhase1 = false) {
    if (datasetState.selectedId === dataset.id && datasetState.status === 'complete') {
      setDatasetState({ status: 'idle', selectedId: '', selectedDataset: null, data: null, error: '' })
      return
    }

    setDatasetState({ status: 'loading', selectedId: dataset.id, selectedDataset: { ...dataset, isPhase1 }, data: null, error: '' })
    try {
      const data = await (isPhase1 ? getPhase1DatasetPreview(dataset.id) : getDatasetPreview(dataset.id))
      setDatasetState({ status: 'complete', selectedId: dataset.id, selectedDataset: { ...dataset, isPhase1 }, data, error: '' })
    } catch (requestError) {
      setDatasetState({
        status: 'error',
        selectedId: dataset.id,
        selectedDataset: { ...dataset, isPhase1 },
        data: null,
        error: requestError.response?.data?.detail || 'Unable to load the dataset preview. Please try again later.',
      })
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal">Data fusion</p>
        <h2 className="mt-2 text-3xl font-bold tracking-tight text-navy">How your assessment data is combined.</h2>
        <p className="mt-3 max-w-3xl leading-7 text-slate-600">CardioCare uses a pseudonymous Patient ID as the fusion key to link a patient record with its calculated signals. It then adds three calculated signals to the submitted health details before estimating cardiovascular risk.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_auto_1fr] lg:items-stretch">
        <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-bold text-navy">Your submitted inputs</p>
          <div className="mt-5 space-y-5">
            {rawInputs.map((group) => (
              <div key={group.title}>
                <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">{group.title}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {group.items.map((item) => <span key={item} className="rounded-full bg-mint px-3 py-1.5 text-xs font-semibold text-teal">{item}</span>)}
                </div>
              </div>
            ))}
          </div>
        </section>

        <div className="grid place-items-center" aria-hidden="true">
          <span className="grid h-12 w-12 place-items-center rounded-full bg-teal text-2xl text-white">+</span>
        </div>

        <section className="rounded-2xl bg-navy p-6 text-white shadow-sm">
          <p className="text-sm font-bold">Fused model data</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">The Patient ID links the record during fusion but is excluded from the model. The calculated signals give the model additional context from related measurements.</p>
          <div className="mt-5 space-y-3">
            {fusedSignals.map((signal) => (
              <div key={signal.name} className="rounded-xl bg-white/10 p-4">
                <p className="font-semibold">{signal.name}</p>
                <p className="mt-1 font-mono text-xs text-teal-200">{signal.formula}</p>
                <p className="mt-2 text-sm leading-5 text-slate-300">{signal.description}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="rounded-2xl border border-teal/20 bg-white p-6 shadow-sm">
        <div className="max-w-3xl">
          <p className="text-sm font-bold text-navy">Phase 1 API-fusion datasets</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">The original heart-failure data is enriched with standard LOINC laboratory metadata from the NLM Clinical Tables API. Select a dataset to preview the records used in the Phase 1 report.</p>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-3">
          {phase1Datasets.map((dataset) => (
            <article key={dataset.filename} className="rounded-xl border border-slate-200 bg-mint/30 p-4">
              <p className="font-mono text-xs font-semibold text-teal">{dataset.filename}</p>
              <p className="mt-3 text-sm font-bold text-navy">{dataset.source}</p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{dataset.description}</p>
              <button type="button" onClick={() => showDataset(dataset, true)} disabled={datasetState.status === 'loading'} className="mt-4 rounded-lg bg-teal px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal/90 disabled:cursor-not-allowed disabled:opacity-60">
                {datasetState.status === 'loading' && datasetState.selectedId === dataset.id ? 'Loading...' : datasetState.status === 'complete' && datasetState.selectedId === dataset.id ? 'Hide data' : 'Show data'}
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="max-w-3xl">
          <p className="text-sm font-bold text-navy">Saved datasets</p>
          <p className="mt-2 text-sm leading-6 text-slate-600">Fused assessments and external searches are stored as CSV records in the dataset folder. Each row includes a timestamp, endpoint, request JSON, and response JSON.</p>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {externalDatasets.map((dataset) => (
            <article key={dataset.filename} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="font-mono text-xs font-semibold text-teal">{dataset.filename}</p>
              <p className="mt-3 text-sm font-bold text-navy">{dataset.source}</p>
              <p className="mt-1 text-sm leading-5 text-slate-600">{dataset.description}</p>
              <button type="button" onClick={() => showDataset(dataset)} disabled={datasetState.status === 'loading'} className="mt-4 rounded-lg bg-teal px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal/90 disabled:cursor-not-allowed disabled:opacity-60">
                {datasetState.status === 'loading' && datasetState.selectedId === dataset.id ? 'Loading...' : datasetState.status === 'complete' && datasetState.selectedId === dataset.id ? 'Hide data' : 'Show data'}
              </button>
            </article>
          ))}
        </div>
        {datasetState.error && <p role="alert" className="mt-5 rounded-xl bg-red-50 p-3 text-sm text-red-800">{datasetState.error}</p>}
        {datasetState.status === 'complete' && (
          <div className="mt-5 rounded-xl border border-slate-200">
            <div className="border-b border-slate-200 bg-slate-50 px-4 py-3">
              <p className="text-sm font-semibold text-navy">{datasetState.selectedDataset.source} · {datasetState.data.record_count} record{datasetState.data.record_count === 1 ? '' : 's'} · showing {datasetState.data.rows.length}</p>
            </div>
            {datasetState.data.rows.length === 0 ? (
              <p className="p-4 text-sm text-slate-600">No records have been saved for this dataset yet.</p>
            ) : datasetState.selectedDataset.isPhase1 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-left text-xs text-slate-700">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>{datasetState.data.columns.map((column) => <th key={column} className="whitespace-nowrap px-4 py-3 font-semibold">{column}</th>)}</tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {datasetState.data.rows.map((row, index) => (
                      <tr key={index}>{datasetState.data.columns.map((column) => <td key={column} className="whitespace-nowrap px-4 py-3">{row[column] || '—'}</td>)}</tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="divide-y divide-slate-200">
                {datasetState.data.rows.map((row, index) => (
                  <article key={`${row.timestamp}-${index}`} className="grid gap-4 p-4 lg:grid-cols-[180px_1fr_1fr]">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">Saved</p>
                      <p className="mt-1 text-sm font-medium text-navy">{new Date(row.timestamp).toLocaleString()}</p>
                      <p className="mt-1 font-mono text-xs text-slate-500">{row.endpoint}</p>
                    </div>
                    <DatasetValue title="Request" value={row.request} />
                    <DatasetValue title="Response" value={row.response} />
                  </article>
                ))}
              </div>
            )}
          </div>
        )}
      </section>

    </div>
  )
}

function DatasetValue({ title, value }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-400">{title}</p>
      <pre className="mt-1 max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-slate-100 p-3 text-xs leading-5 text-slate-700">{JSON.stringify(value, null, 2)}</pre>
    </div>
  )
}

export default DataFusion
