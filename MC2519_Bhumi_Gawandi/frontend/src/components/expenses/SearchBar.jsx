import { Search, X } from "lucide-react";

function SearchBar({
  searchTerm,
  setSearchTerm,
}) {
  const clearSearch = () => {
    setSearchTerm("");
  };

  return (
    <div className="expense-search">

      <Search
        size={19}
        className="expense-search-icon"
      />

      <input
        type="text"
        placeholder="Search by expense title..."
        value={searchTerm}
        onChange={(e) =>
          setSearchTerm(e.target.value)
        }
      />

      {searchTerm && (
        <button
          type="button"
          onClick={clearSearch}
          className="expense-search-clear"
          aria-label="Clear search"
        >
          <X size={17} />
        </button>
      )}

    </div>
  );
}

export default SearchBar;