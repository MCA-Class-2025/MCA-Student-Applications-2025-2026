import { 
  LayoutDashboard, 
  Wallet, 
  PlusCircle, 
  Target, 
  Tags, 
  BarChart3, 
  Bot, 
  ScanLine, 
  Mic, 
} from "lucide-react"; 
 
import { NavLink } from "react-router-dom"; 
 
 
function Sidebar() { 
 
  const menuItems = [ 
    { 
      name: "Dashboard", 
      path: "/dashboard", 
      icon: LayoutDashboard, 
    }, 
    { 
      name: "Expenses", 
      path: "/expenses", 
      icon: Wallet, 
    }, 
    { 
      name: "Add Expense", 
      path: "/add-expense", 
      icon: PlusCircle, 
    }, 
    { 
      name: "Budget", 
      path: "/budget", 
      icon: Target, 
    }, 
    { 
      name: "Categories", 
      path: "/categories", 
      icon: Tags, 
    }, 
    { 
      name: "Reports", 
      path: "/reports", 
      icon: BarChart3, 
    }, 

    // =====================================================
    // DATA & ANALYTICS
    // =====================================================
    {
      name: "Data & Analytics",
      path: "/data-analytics",
      icon: BarChart3,
    },

    { 
      name: "AI Assistant", 
      path: "/ai-assistant", 
      icon: Bot, 
    }, 
    { 
      name: "Receipt Scanner", 
      path: "/receipt-scanner", 
      icon: ScanLine, 
    }, 
    { 
      name: "Voice Entry", 
      path: "/voice-entry", 
      icon: Mic, 
    }, 
  ]; 
 
 
  return ( 
 
    <aside 
      className=" 
        w-full 
        h-full 
        min-h-screen 
        bg-[#12172B] 
        flex 
        flex-col 
      " 
    > 
 
      {/* ===================================================== 
          LOGO 
      ====================================================== */} 
 
      <div 
        className=" 
          h-[125px] 
          flex 
          items-center 
          justify-center 
          border-b 
          border-[#2D3248] 
          flex-shrink-0 
        " 
      > 
 
        <NavLink 
          to="/dashboard" 
          className="no-underline" 
        > 
 
          <h1 
            className=" 
              text-[36px] 
              font-medium 
              leading-none 
              tracking-[-2px] 
              whitespace-nowrap 
            " 
            style={{ 
              fontFamily: "Fraunces, serif", 
            }} 
          > 
 
            <span className="text-[#F6F4EE]"> 
              SpendSmart 
            </span> 
 
            <span className="text-[#2CC295]"> 
              .ai 
            </span> 
 
          </h1> 
 
        </NavLink> 
 
      </div> 
 
 
      {/* ===================================================== 
          MENU 
      ====================================================== */} 
 
      <div className="flex-1 px-5 pt-7 overflow-y-auto"> 
 
        <nav className="space-y-2"> 
 
          {menuItems.map((item) => { 
 
            const Icon = item.icon; 
 
            return ( 
 
              <NavLink 
                key={item.name} 
                to={item.path} 
                className={({ isActive }) => ` 
                  w-full 
                  h-[50px] 
                  px-5 
                  flex 
                  items-center 
                  gap-4 
                  rounded-xl 
                  no-underline 
                  transition-all 
                  duration-200 
 
                  ${ 
                    isActive 
                      ? "bg-[#1F6F5C] text-white" 
                      : "text-[#C5C9D5] hover:bg-[#1C2135] hover:text-white" 
                  } 
                `} 
              > 
 
                <Icon 
                  size={22} 
                  strokeWidth={2} 
                  className="flex-shrink-0" 
                /> 
 
                <span 
                  className=" 
                    text-[16px] 
                    font-semibold 
                    whitespace-nowrap 
                  " 
                > 
                  {item.name} 
                </span> 
 
              </NavLink> 
 
            ); 
 
          })} 
 
        </nav> 
 
      </div> 
 
 
      {/* ===================================================== 
          FOOTER 
      ====================================================== */} 
 
      <div 
        className=" 
          h-[78px] 
          flex-shrink-0 
          border-t 
          border-[#2D3248] 
          flex 
          items-center 
          justify-center 
        " 
      > 
 
        <div className="text-center"> 
 
          <p 
            className=" 
              text-[11px] 
              text-[#8F96AA] 
            " 
          > 
            <b>Developed by</b> 
          </p> 
 
          <p 
            className=" 
              text-sm 
              font-semibold 
              text-[#2CC295] 
              mt-1 
            " 
          > 
            Bhumi Gawandi 
          </p> 
 
        </div> 
 
      </div> 
 
    </aside> 
 
  ); 
} 
 
 
export default Sidebar;