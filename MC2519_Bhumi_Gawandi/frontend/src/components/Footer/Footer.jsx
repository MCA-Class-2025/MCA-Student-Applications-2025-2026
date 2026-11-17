function Footer() {
  const columns = [
    {
      title: "Product",
      links: ["Features", "Pricing", "AI assistant", "Security"],
    },
    {
      title: "Company",
      links: ["About", "Careers", "Blog", "Contact"],
    },
    {
      title: "Resources",
      links: ["Help center", "Documentation", "API", "Community"],
    },
  ];

  const socials = [
    { label: "X", icon: <path d="M4 4l16 16M20 4L4 20" /> },
    {
      label: "LinkedIn",
      icon: (
        <>
          <rect x="3" y="9" width="4" height="12" />
          <circle cx="5" cy="4" r="2" />
          <path d="M11 9v12M11 13a4 4 0 018 0v8" />
        </>
      ),
    },
    {
      label: "GitHub",
      icon: (
        <path d="M12 2a10 10 0 00-3.16 19.49c.5.1.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.46-1.16-1.11-1.47-1.11-1.47-.9-.62.07-.6.07-.6 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.56-1.11-4.56-4.94 0-1.1.39-1.99 1.03-2.69-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 015 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.69 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0012 2z" />
      ),
    },
  ];

  return (
    // left-1/2 + -ml-[50vw] is a "full-bleed breakout": it forces this element to span
    // the full viewport width edge-to-edge even if a parent wrapper has max-w/mx-auto
    // constraints on it (which is why the footer was sitting "in the middle" before).
    <footer
      id="contact"
      className="relative left-1/2 right-1/2 -ml-[50vw] -mr-[50vw] w-screen bg-[#12172B] text-[#F6F4EE]"
    >
      <div className="w-full px-8 md:px-14 pt-16 pb-8">

        {/* Top row: brand block + link columns, aligned to a shared baseline */}
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-12">

          {/* Brand */}
          <div className="text-left md:w-72 md:shrink-0">
            <div className="flex items-center gap-2.5">
              <span className="w-7 h-7 rounded-md flex items-center justify-center shrink-0" style={{ backgroundColor: "#1F6F5C" }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#F6F4EE" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 19V5a1 1 0 011-1h9l6 6v9a1 1 0 01-1 1H5a1 1 0 01-1-1z" />
                  <path d="M8 12h8M8 16h5" />
                </svg>
              </span>
              <span className="font-medium text-lg" style={{ fontFamily: "'Fraunces', serif" }}>
                SpendSmart<span style={{ color: "#4FAE93" }}>.ai</span>
              </span>
            </div>

            <p className="mt-4 text-sm text-[#8B897F] leading-relaxed text-left">
              Track spending, plan budgets, and get plain-language insights from your AI assistant.
            </p>

            <div className="flex gap-3 mt-6">
              {socials.map((s) => (
                <a
                  key={s.label}
                  href="#"
                  aria-label={s.label}
                  className="w-9 h-9 rounded-md border border-[#2A3040] flex items-center justify-center text-[#B8B6AE] hover:text-[#F6F4EE] hover:border-[#1F6F5C] transition-colors"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                    {s.icon}
                  </svg>
                </a>
              ))}
            </div>
          </div>

          {/* Link columns, evenly spaced, same top baseline as brand block */}
          <div className="flex-1 flex flex-col sm:flex-row sm:justify-between gap-10">
            {columns.map((col) => (
              <div key={col.title} className="text-left sm:w-40">
                <h4 className="text-xs font-semibold tracking-widest uppercase text-[#6B7180] mb-4">
                  {col.title}
                </h4>
                <ul className="space-y-3">
                  {col.links.map((link) => (
                    <li key={link}>
                      <a href="#" className="text-sm text-[#B8B6AE] hover:text-[#F6F4EE] transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

        </div>

        {/* Bottom bar, edges aligned with the content above */}
        <div className="border-t border-[#232838] mt-12 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-[#6B7180] text-left">
            &copy; 2026 SpendSmart.ai. All rights reserved.
          </p>
          <div className="flex gap-6 text-sm text-[#6B7180]">
            <a href="#" className="hover:text-[#F6F4EE] transition-colors">Privacy policy</a>
            <a href="#" className="hover:text-[#F6F4EE] transition-colors">Terms of service</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;