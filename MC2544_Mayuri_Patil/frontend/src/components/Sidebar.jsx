const navigation = [
  { id: 'overview', label: 'Overview', icon: '⌂' },
  { id: 'assessment', label: 'Risk assessment', icon: '♥' },
  { id: 'data-fusion', label: 'Data fusion', icon: '⟲' },
  { id: 'phase2-rag', label: 'Phase 2 RAG', icon: '✦' },
  { id: 'library', label: 'Health library', icon: '⌕' },
  { id: 'nearby-care', label: 'Nearby care', icon: '⌖' },
]

function Sidebar({ activeTab, isOpen, onClose, onSelectTab }) {
  function selectTab(tab) {
    onSelectTab(tab)
    onClose()
  }

  return (
    <>
      <button
        type="button"
        aria-label="Close navigation"
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-navy/40 transition lg:hidden ${isOpen ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
      />
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-72 -translate-x-full flex-col border-r border-slate-200 bg-white p-5 shadow-2xl transition-transform duration-200 lg:translate-x-0 lg:shadow-none ${isOpen ? 'translate-x-0' : ''}`}>
        <div className="flex items-center justify-between px-2 py-2">
          <button type="button" className="flex items-center gap-2 text-xl font-bold tracking-tight text-navy" onClick={() => selectTab('overview')}>
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-teal font-serif text-xl text-white">+</span>
            Cardio<span className="text-teal">Care</span>
          </button>
          <button type="button" aria-label="Close navigation" onClick={onClose} className="grid h-9 w-9 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 lg:hidden">×</button>
        </div>

        <nav aria-label="Main navigation" className="mt-10 space-y-2">
          <p className="px-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Menu</p>
          {navigation.map((item) => (
            <button key={item.id} type="button" onClick={() => selectTab(item.id)} aria-current={activeTab === item.id ? 'page' : undefined} className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-semibold transition focus:outline-none ${activeTab === item.id ? 'bg-mint text-teal' : 'text-slate-600 hover:bg-mint hover:text-teal focus:bg-mint focus:text-teal'}`}>
              <span className="grid h-7 w-7 place-items-center rounded-lg bg-slate-100 text-base text-teal" aria-hidden="true">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="mt-auto rounded-2xl bg-mint p-4">
          <p className="text-sm font-bold text-navy">A healthier heart starts today.</p>
          <p className="mt-2 text-xs leading-5 text-slate-600">Use your assessment to understand your next wellness step.</p>
          <button type="button" onClick={() => selectTab('assessment')} className="mt-4 inline-flex rounded-lg bg-teal px-3 py-2 text-xs font-semibold text-white transition hover:bg-teal/90">Start assessment</button>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
