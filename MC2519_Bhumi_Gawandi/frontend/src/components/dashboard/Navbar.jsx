import { Bell, Search, User } from "lucide-react";

function Navbar() {
  return (
    <header className="h-20 bg-white border-b border-gray-200 flex items-center justify-between px-8">

      <div>
        <h2 className="text-3xl font-bold text-[#12172B]">
          Dashboard
        </h2>
        <p className="text-gray-500 text-sm">
          Welcome back, Bhumi 👋
        </p>
      </div>

      <div className="flex items-center gap-6">

        <div className="relative">

          <Search
            className="absolute left-4 top-3 text-gray-400"
            size={18}
          />

          <input
            type="text"
            placeholder="Search expenses..."
            className="w-80 bg-[#F6F4EE] rounded-xl pl-12 pr-4 py-3 outline-none"
          />

        </div>

        <button className="relative">

          <Bell size={24} />

          <span className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full"></span>

        </button>

        <div className="w-11 h-11 rounded-full bg-[#1F6F5C] flex items-center justify-center text-white">

          <User size={20} />

        </div>

      </div>

    </header>
  );
}

export default Navbar;