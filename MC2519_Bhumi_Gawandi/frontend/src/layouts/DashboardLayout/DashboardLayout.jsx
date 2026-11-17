import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

function DashboardLayout({ children }) {
  return (
    <div className="dashboard-layout">

      {/* SIDEBAR */}
      <aside className="dashboard-sidebar">
        <Sidebar />
      </aside>

      {/* RIGHT SIDE */}
      <div className="dashboard-main">

        {/* NAVBAR */}
        <DashboardNavbar />

        {/* PAGE CONTENT */}
        <main className="dashboard-content">
          {children}
        </main>

      </div>

    </div>
  );
}

export default DashboardLayout;