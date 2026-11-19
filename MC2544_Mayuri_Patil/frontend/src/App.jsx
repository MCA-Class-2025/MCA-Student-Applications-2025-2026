import { useState } from 'react'
import AppHeader from './components/AppHeader'
import Sidebar from './components/Sidebar'
import AssessmentForm from './components/AssessmentForm'
import AssessmentResult from './components/AssessmentResult'
import DataFusion from './components/DataFusion'
import NearbyCare from './components/NearbyCare'
import Phase2Rag from './components/Phase2Rag'
import ResourceSearch from './components/ResourceSearch'
import { askPhase2Question, findNearbyCare, getRecommendations, predictRisk, searchDrugLabels, searchFoods, searchPackagedFoods } from './services/api'

function App() {
  const [values, setValues] = useState({})
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')
  const [riskState, setRiskState] = useState({ status: 'idle', result: null, error: '' })
  const [guidanceState, setGuidanceState] = useState({ status: 'idle', recommendation: null, error: '' })

  const updateValue = (name, value) => setValues((current) => ({ ...current, [name]: value }))
  const createPayload = () => Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, key === 'patient_id' ? value : Number(value)]),
  )

  async function handleSubmit(event) {
    event.preventDefault()
    setRiskState({ status: 'loading', result: null, error: '' })
    setGuidanceState({ status: 'idle', recommendation: null, error: '' })

    try {
      const result = await predictRisk(createPayload())
      setRiskState({ status: 'complete', result, error: '' })
    } catch (requestError) {
      setRiskState({
        status: 'error',
        result: null,
        error: requestError.response?.data?.detail || 'Unable to reach the prediction service. Please try again later.',
      })
    }
  }

  async function handleRecommendations() {
    setGuidanceState({ status: 'loading', recommendation: null, error: '' })

    try {
      const recommendation = await getRecommendations(createPayload())
      setGuidanceState({ status: 'complete', recommendation, error: '' })
    } catch (requestError) {
      setGuidanceState({
        status: 'error',
        recommendation: null,
        error: requestError.response?.data?.detail || 'Unable to generate recommendations. Please try again later.',
      })
    }
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar activeTab={activeTab} isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} onSelectTab={setActiveTab} />
      <main className="min-h-screen lg:pl-72">
        <AppHeader onOpenSidebar={() => setIsSidebarOpen(true)} />

        <section className="mx-auto max-w-7xl px-5 py-10 sm:py-14">
          {activeTab === 'overview' && (
            <div className="grid gap-8 rounded-[2rem] bg-navy px-6 py-9 text-white shadow-xl shadow-slate-300/50 sm:px-10 lg:grid-cols-[1fr_auto] lg:items-end">
              <div className="max-w-2xl">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-200">Your heart health, made simple</p>
                <h1 className="mt-4 text-4xl font-bold tracking-tight sm:text-5xl">Know your heart health. Take your next step with confidence.</h1>
                <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300 sm:text-lg">Get a personalized cardiovascular risk estimate, practical wellness guidance, and trusted tools to support healthier daily choices.</p>
              </div>
              <button type="button" onClick={() => setActiveTab('assessment')} className="rounded-xl bg-teal px-5 py-3 font-semibold text-white transition hover:bg-teal/90">Start your assessment</button>
            </div>
          )}

          {activeTab === 'assessment' && (
            <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_360px]">
              <AssessmentForm values={values} onValueChange={updateValue} onSubmit={handleSubmit} status={riskState.status} />
              <AssessmentResult
                result={riskState.result}
                error={riskState.error}
                guidance={guidanceState.recommendation}
                guidanceError={guidanceState.error}
                guidanceStatus={guidanceState.status}
                onGetGuidance={handleRecommendations}
              />
            </div>
          )}

          {activeTab === 'data-fusion' && <DataFusion />}

          {activeTab === 'phase2-rag' && <Phase2Rag askPhase2Question={askPhase2Question} />}

          {activeTab === 'library' && (
            <div>
          <div className="mb-6">
            <p className="text-sm font-semibold uppercase tracking-[0.16em] text-teal">Health library</p>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-navy">Make informed everyday choices.</h2>
          </div>
          <div className="grid gap-6 xl:grid-cols-3">
            <ResourceSearch
              type="food"
              eyebrow="USDA FoodData Central"
              title="Food nutrition"
              description="Find calorie and food category details for everyday ingredients."
              placeholder="Try oats, apple, spinach"
              search={searchFoods}
            />
            <ResourceSearch
              type="drug"
              eyebrow="FDA drug labels"
              title="Medication information"
              description="Look up purpose and warning information by brand name."
              placeholder="Try aspirin or Lipitor"
              search={searchDrugLabels}
            />
            <ResourceSearch
              type="packaged"
              eyebrow="Open Food Facts"
              title="Packaged food check"
              description="Compare nutrition grades and key values per 100 grams."
              placeholder="Try cereal or potato chips"
              search={searchPackagedFoods}
            />
          </div>
            </div>
          )}

          {activeTab === 'nearby-care' && <NearbyCare findNearbyCare={findNearbyCare} />}
        </section>
      </main>
    </div>
  )
}

export default App
