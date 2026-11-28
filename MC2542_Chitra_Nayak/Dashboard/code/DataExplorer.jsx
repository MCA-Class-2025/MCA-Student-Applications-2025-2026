import { Fragment, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API = "http://127.0.0.1:5000/api/dashboard";
const FIELDS = ["Id", "title", "year", "authors", "citations", "source", "document_type", "publication_name", "topic", "category"];
const HEADINGS = { Id: "Record ID", title: "Research title", year: "Year", authors: "Authors", citations: "Citations", source: "Source", document_type: "Type", publication_name: "Publication", topic: "Topic", category: "Category" };

function displayValue(value, field) {
    if (value === null || value === undefined || String(value).trim() === "") return "—";
    const raw = String(value);
    if (field === "authors" && raw.startsWith("[") && raw.endsWith("]")) {
        return raw.slice(1, -1).replace(/['"]/g, "").replace(/,\s*/g, ", ");
    }
    return raw;
}

export default function DataExplorer() {
    const navigate = useNavigate();
    const [records, setRecords] = useState([]);
    const [columns, setColumns] = useState([]);
    const [options, setOptions] = useState({ sources: [], years: [] });
    const [source, setSource] = useState("");
    const [year, setYear] = useState("");
    const [search, setSearch] = useState("");
    const [query, setQuery] = useState("");
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalPages, setTotalPages] = useState(1);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [sortColumn, setSortColumn] = useState("");
    const [sortDirection, setSortDirection] = useState("asc");
    const [expanded, setExpanded] = useState(null);

    useEffect(() => {
        const controller = new AbortController();
        fetch(`${API}/overview`, { signal: controller.signal })
            .then(r => { if (!r.ok) throw new Error("Unable to load filter options"); return r.json(); })
            .then(result => { if (result.success && result.filters) setOptions(result.filters); })
            .catch(err => { if (err.name !== "AbortError") setError(err.message); });
        return () => controller.abort();
    }, []);

    useEffect(() => {
        const controller = new AbortController();
        async function loadRecords() {
            setLoading(true);
            setError("");
            const params = new URLSearchParams({
                page: String(page), page_size: String(pageSize), search: query,
                source, year, sort_by: sortColumn, sort_direction: sortDirection
            });
            try {
                const response = await fetch(`${API}/records?${params}`, { signal: controller.signal });
                if (!response.ok) throw new Error("Unable to load dataset records.");
                const result = await response.json();
                if (!result.success) throw new Error(result.error || "Dashboard API error.");
                if (controller.signal.aborted) return;
                setRecords(result.records || []);
                setColumns(result.columns || []);
                setTotal(result.total || 0);
                setTotalPages(Math.max(1, result.total_pages || 1));
            } catch (err) {
                if (err.name !== "AbortError") setError(err.message);
            } finally {
                if (!controller.signal.aborted) setLoading(false);
            }
        }
        loadRecords();
        return () => controller.abort();
    }, [page, pageSize, query, source, year, sortColumn, sortDirection]);

    const visibleColumns = FIELDS.filter(field => columns.includes(field));
    const resetPage = () => { setPage(1); setExpanded(null); };
    function handleSort(column) {
        if (sortColumn === column) setSortDirection(previous => previous === "asc" ? "desc" : "asc");
        else { setSortColumn(column); setSortDirection("asc"); }
        resetPage();
    }
    function resetFilters() {
        setSource(""); setYear(""); setSearch(""); setQuery("");
        setSortColumn(""); setSortDirection("asc"); resetPage();
    }
    const firstRecord = total === 0 ? 0 : (page - 1) * pageSize + 1;
    const lastRecord = Math.min(total, page * pageSize);

    return (
        <div className="explorer-page">
            <style>{`
                .explorer-page{min-height:100vh;background:#f0f5fb;padding:32px clamp(18px,3.5vw,64px);font-family:Inter,Arial,sans-serif;color:#12213a;box-sizing:border-box}
                .explorer-page *{box-sizing:border-box}
                .explorer-nav{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:34px}
                .explorer-nav button,.explorer-button{padding:13px 22px;border:1px solid #d2deec;border-radius:11px;background:white;color:#213651;font-size:14px;cursor:pointer}
                .explorer-nav .active,.explorer-button.primary{background:#2052db;color:white;border-color:#2052db;font-weight:600}
                .explorer-kicker{color:#2052db;letter-spacing:2px;font-size:12px;font-weight:800}
                .explorer-head{display:flex;justify-content:space-between;align-items:flex-end;gap:18px;flex-wrap:wrap;margin:14px 0 25px}
                .explorer-head h1{font-size:clamp(26px,3vw,36px);margin:0 0 7px}
                .explorer-muted{color:#627894;margin:0}
                .explorer-panel,.explorer-table-card{background:white;border:1px solid #e1e9f3;border-radius:19px;padding:23px;margin-bottom:22px;box-shadow:0 6px 26px rgba(23,46,79,.035)}
                .explorer-filters{display:flex;align-items:end;gap:15px;flex-wrap:wrap}
                .explorer-field{display:flex;flex-direction:column;gap:8px;min-width:170px;flex:1}
                .explorer-field label{font-size:13px;font-weight:700}
                .explorer-field input,.explorer-field select{height:45px;border:1px solid #cbd8e8;border-radius:10px;padding:0 13px;background:white;color:#172b45;font-size:14px;width:100%}
                .explorer-search{flex:3;min-width:250px}
                .explorer-button{height:45px;white-space:nowrap}
                .explorer-button:disabled{opacity:.45;cursor:not-allowed}
                .explorer-meta{display:flex;justify-content:space-between;align-items:center;gap:15px;flex-wrap:wrap;margin-bottom:16px}
                .explorer-meta strong{font-size:22px}
                .explorer-scroll{overflow:auto;max-width:100%}
                .explorer-table{width:100%;border-collapse:collapse;min-width:1150px;font-size:13px}
                .explorer-table th{position:sticky;top:0;background:#eaf1ff;color:#243b5d;text-align:left;padding:15px 13px;border-bottom:1px solid #cddbee;white-space:nowrap}
                .explorer-table th button{background:none;border:0;color:inherit;font:inherit;font-weight:700;cursor:pointer;padding:0;text-align:left}
                .explorer-table td{padding:13px;border-bottom:1px solid #e8eef6;max-width:270px;vertical-align:top}
                .explorer-table tbody tr:hover{background:#f6f9ff}
                .explorer-cell{max-width:270px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
                .explorer-table tr.expanded .explorer-cell{white-space:normal;overflow-wrap:anywhere}
                .explorer-details{background:#f6f9ff;padding:15px 18px;border-radius:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
                .explorer-details div{overflow-wrap:anywhere;line-height:1.5}
                .explorer-details strong{display:block;margin-bottom:3px;color:#4a6487;font-size:12px}
                .explorer-details a{color:#2052db}
                .explorer-expand{background:#e9f0ff;border:0;border-radius:7px;padding:6px 9px;color:#2052db;cursor:pointer;font-size:12px}
                .explorer-bottom{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:14px;margin-top:20px}
                .explorer-pages{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
                .explorer-note{font-size:12px;color:#637996;margin-top:17px}
                .explorer-error{color:#b42318;margin:14px 0}
                @media(max-width:720px){.explorer-page{padding:20px 14px}.explorer-panel,.explorer-table-card{padding:15px}.explorer-field{min-width:100%}}
            `}</style>
            <nav className="explorer-nav">
                <button onClick={() => navigate("/dsaa-dashboard")}>Analytics Dashboard</button>
                <button className="active" onClick={() => navigate("/dsaa-data-explorer")}>Data Explorer</button>
                <button onClick={() => navigate("/")}>ResearchIQ Home</button>
            </nav>
            <span className="explorer-kicker">RESEARCHIQ / DATA INTELLIGENCE</span>
            <div className="explorer-head">
                <div><h1>DSAA Data Explorer</h1><p className="explorer-muted">Search, filter, sort and inspect the fused research dataset</p></div>
                <button className="explorer-button" onClick={resetFilters}>Reset filters</button>
            </div>
            <section className="explorer-panel">
                <form className="explorer-filters" onSubmit={event => { event.preventDefault(); setQuery(search.trim()); resetPage(); }}>
                    <div className="explorer-field explorer-search"><label htmlFor="explorer-search">Search all fields</label><input id="explorer-search" value={search} onChange={event => setSearch(event.target.value)} placeholder="e.g. Machine Learning" /></div>
                    <div className="explorer-field"><label htmlFor="explorer-source">Data source</label><select id="explorer-source" value={source} onChange={event => { setSource(event.target.value); resetPage(); }}><option value="">All sources</option>{options.sources.map(item => <option key={item} value={item}>{item}</option>)}</select></div>
                    <div className="explorer-field"><label htmlFor="explorer-year">Publication year</label><select id="explorer-year" value={year} onChange={event => { setYear(event.target.value); resetPage(); }}><option value="">All years</option>{options.years.map(item => <option key={item} value={String(item)}>{item}</option>)}</select></div>
                    <button className="explorer-button primary" type="submit">Search</button>
                    <button className="explorer-button" type="button" onClick={() => { setSearch(""); setQuery(""); resetPage(); }}>Clear search</button>
                </form>
            </section>
            <section className="explorer-table-card">
                <div className="explorer-meta"><div><strong>{total.toLocaleString()}</strong> <span className="explorer-muted">matching records</span></div><div className="explorer-muted">Showing {firstRecord}–{lastRecord} of {total.toLocaleString()}</div></div>
                {error && <p className="explorer-error" role="alert">{error}</p>}
                {loading ? <p>Loading records...</p> : <div className="explorer-scroll"><table className="explorer-table"><thead><tr><th>Details</th>{visibleColumns.map(column => <th key={column}><button type="button" onClick={() => handleSort(column)} title={`Sort by ${HEADINGS[column] || column}`}>{HEADINGS[column] || column}{sortColumn === column ? (sortDirection === "asc" ? " ▲" : " ▼") : " ↕"}</button></th>)}</tr></thead><tbody>{records.map((record, index) => { const key = `${record.Id ?? "row"}-${index}`; const isOpen = expanded === key; return <Fragment key={key}><tr className={isOpen ? "expanded" : ""}><td><button className="explorer-expand" type="button" onClick={() => setExpanded(isOpen ? null : key)} aria-expanded={isOpen}>{isOpen ? "Close" : "View"}</button></td>{visibleColumns.map(column => <td key={column}><div className="explorer-cell" title={displayValue(record[column], column)}>{displayValue(record[column], column)}</div></td>)}</tr>{isOpen && <tr key={`${key}-details`}><td colSpan={visibleColumns.length + 1}><div className="explorer-details">{visibleColumns.map(column => <div key={column}><strong>{HEADINGS[column] || column}</strong>{displayValue(record[column], column)}</div>)}{["link", "dataset_url", "pdf_url"].filter(field => typeof record[field] === "string" && /^https?:\/\//i.test(record[field])).map(field => <div key={field}><strong>{field.replaceAll("_", " ")}</strong><a href={record[field]} target="_blank" rel="noreferrer">Open resource</a></div>)}</div></td></tr>}</Fragment>; })}</tbody></table>{records.length === 0 && <p style={{padding:20}}>No matching records found.</p>}</div>}
                <div className="explorer-bottom"><div className="explorer-pages"><button className="explorer-button" disabled={page <= 1 || loading} onClick={() => { setPage(1); setExpanded(null); }}>First</button><button className="explorer-button" disabled={page <= 1 || loading} onClick={() => { setPage(p => p - 1); setExpanded(null); }}>Previous</button><span>Page {page} of {totalPages}</span><button className="explorer-button" disabled={page >= totalPages || loading} onClick={() => { setPage(p => p + 1); setExpanded(null); }}>Next</button><button className="explorer-button" disabled={page >= totalPages || loading} onClick={() => { setPage(totalPages); setExpanded(null); }}>Last</button></div><label className="explorer-muted">Rows per page: <select value={pageSize} onChange={event => { setPageSize(Number(event.target.value)); resetPage(); }}><option value={10}>10</option><option value={20}>20</option><option value={50}>50</option></select></label></div>
                <p className="explorer-note">Sorting applies to all matching records before pagination. Publication-year sorting uses the Python Merge Sort implementation. Empty fields may reflect different source schemas.</p>
            </section>
        </div>
    );
}
