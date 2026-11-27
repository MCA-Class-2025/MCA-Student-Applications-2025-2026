function AppHeader({ onOpenSidebar }) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <button type="button" onClick={onOpenSidebar} aria-label="Open navigation" className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 text-xl text-navy transition hover:bg-mint lg:hidden">☰</button>
        <p className="hidden text-sm font-semibold text-slate-500 lg:block">Your personal heart health dashboard</p>
        <span className="rounded-full bg-mint px-3 py-1.5 text-xs font-semibold text-teal">Health companion</span>
      </div>
    </header>
  )
}

export default AppHeader
