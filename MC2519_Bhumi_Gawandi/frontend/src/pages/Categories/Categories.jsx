import { useEffect, useState } from "react";

import {
  Plus,
  Pencil,
  Trash2,
  Tags,
  X,
} from "lucide-react";

import toast from "react-hot-toast";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import {
  getCategories,
  createCategory,
  updateCategory,
  deleteCategory,
} from "../../services/categoryService";


function Categories() {

  // ============================================================
  // STATE
  // ============================================================

  const [categories, setCategories] = useState([]);

  const [loading, setLoading] = useState(true);

  const [showForm, setShowForm] = useState(false);

  const [editingId, setEditingId] = useState(null);

  const [name, setName] = useState("");

  const [description, setDescription] = useState("");

  const [saving, setSaving] = useState(false);


  // ============================================================
  // LOAD CATEGORIES
  // ============================================================

  const loadCategories = async () => {

    try {

      setLoading(true);

      const data = await getCategories();

      console.log(
        "Categories API response:",
        data
      );

      setCategories(
        Array.isArray(data)
          ? data
          : []
      );

    } catch (error) {

      console.error(
        "Category loading error:",
        error
      );

      if (
        error?.response?.status === 401
      ) {

        toast.error(
          "Session expired. Please login again."
        );

        localStorage.removeItem("token");
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");

        window.location.href =
          "/login";

        return;

      }

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to load categories."
      );

    } finally {

      setLoading(false);

    }
  };


  // ============================================================
  // INITIAL LOAD
  // ============================================================

  useEffect(() => {

    loadCategories();

  }, []);


  // ============================================================
  // RESET FORM
  // ============================================================

  const resetForm = () => {

    setName("");

    setDescription("");

    setEditingId(null);

    setShowForm(false);

  };


  // ============================================================
  // OPEN ADD FORM
  // ============================================================

  const handleAdd = () => {

    setEditingId(null);

    setName("");

    setDescription("");

    setShowForm(true);

  };


  // ============================================================
  // EDIT CATEGORY
  // ============================================================

  const handleEdit = (category) => {

    setEditingId(
      category._id
    );

    setName(
      category.name || ""
    );

    setDescription(
      category.description || ""
    );

    setShowForm(true);

  };


  // ============================================================
  // SAVE CATEGORY
  // ============================================================

  const handleSubmit = async (e) => {

    e.preventDefault();

    if (!name.trim()) {

      toast.error(
        "Category name is required."
      );

      return;

    }

    try {

      setSaving(true);

      const categoryData = {

        name:
          name.trim(),

        description:
          description.trim(),

      };


      // UPDATE

      if (editingId) {

        const result =
          await updateCategory(
            editingId,
            categoryData
          );


        if (
          result?.success === false
        ) {

          toast.error(
            result.message ||
            "Unable to update category."
          );

          return;

        }


        toast.success(
          "Category updated successfully."
        );

      }


      // CREATE

      else {

        const result =
          await createCategory(
            categoryData
          );


        if (
          result?.success === false
        ) {

          toast.error(
            result.message ||
            "Unable to create category."
          );

          return;

        }


        toast.success(
          "Category created successfully."
        );

      }


      resetForm();

      await loadCategories();

    } catch (error) {

      console.error(
        "Category save error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to save category."
      );

    } finally {

      setSaving(false);

    }
  };


  // ============================================================
  // DELETE CATEGORY
  // ============================================================

  const handleDelete = async (id) => {

    const confirmed =
      window.confirm(
        "Are you sure you want to delete this category?"
      );

    if (!confirmed) {
      return;
    }


    try {

      const result =
        await deleteCategory(id);


      if (
        result?.success === false
      ) {

        toast.error(
          result.message ||
          "Unable to delete category."
        );

        return;

      }


      toast.success(
        "Category deleted successfully."
      );

      await loadCategories();

    } catch (error) {

      console.error(
        "Delete category error:",
        error
      );

      toast.error(
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        "Unable to delete category."
      );

    }

  };


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {

    return (

      <div className="dashboard-layout">

        <aside className="dashboard-sidebar">

          <Sidebar />

        </aside>


        <div className="dashboard-main">

          <DashboardNavbar />

          <main className="dashboard-content">

            <div className="category-loading">

              <div className="category-spinner" />

              <p>
                Loading categories...
              </p>

            </div>

          </main>

        </div>

      </div>

    );

  }


  // ============================================================
  // UI
  // ============================================================

  return (

    <div className="dashboard-layout">


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="dashboard-sidebar">

        <Sidebar />

      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <div className="dashboard-main">


        {/* ====================================================
            NAVBAR
        ==================================================== */}

        <DashboardNavbar />


        {/* ====================================================
            CONTENT
        ==================================================== */}

        <main className="dashboard-content">

          <div className="category-page">


            {/* ==================================================
                HEADER
            ================================================== */}

            <div className="category-page-header">

              <div>

                <div className="category-title-row">

                  <div className="category-title-icon">

                    <Tags size={22} />

                  </div>

                  <h1>
                    Categories
                  </h1>

                </div>

                <p>
                  Manage your personal expense categories.
                </p>

              </div>


              <button
                type="button"
                onClick={handleAdd}
                className="category-add-button"
              >

                <Plus size={18} />

                Add Category

              </button>

            </div>


            {/* ==================================================
                FORM
            ================================================== */}

            {showForm && (

              <div className="category-form-card">


                <div className="category-form-header">

                  <div>

                    <h2>

                      {editingId
                        ? "Edit Category"
                        : "Create Category"}

                    </h2>

                    <p>
                      Add a category to organize your expenses.
                    </p>

                  </div>


                  <button
                    type="button"
                    onClick={resetForm}
                    className="category-close-button"
                  >

                    <X size={18} />

                  </button>

                </div>


                <form
                  onSubmit={handleSubmit}
                  className="category-form"
                >


                  {/* CATEGORY NAME */}

                  <div className="category-field">

                    <label>
                      Category Name
                    </label>

                    <input
                      type="text"
                      value={name}
                      onChange={(e) =>
                        setName(
                          e.target.value
                        )
                      }
                      placeholder="e.g. Food"
                    />

                  </div>


                  {/* DESCRIPTION */}

                  <div className="category-field">

                    <label>
                      Description
                    </label>

                    <input
                      type="text"
                      value={description}
                      onChange={(e) =>
                        setDescription(
                          e.target.value
                        )
                      }
                      placeholder="e.g. Restaurants and groceries"
                    />

                  </div>


                  {/* ACTIONS */}

                  <div className="category-form-actions">

                    <button
                      type="button"
                      onClick={resetForm}
                      className="category-cancel-button"
                    >
                      Cancel
                    </button>


                    <button
                      type="submit"
                      disabled={saving}
                      className="category-save-button"
                    >

                      {saving
                        ? "Saving..."
                        : editingId
                          ? "Update Category"
                          : "Create Category"}

                    </button>

                  </div>

                </form>

              </div>

            )}


            {/* ==================================================
                CATEGORY LIST
            ================================================== */}

            {categories.length === 0 ? (

              <div className="category-empty">

                <div className="category-empty-icon">

                  <Tags size={30} />

                </div>


                <h2>
                  No Categories Yet
                </h2>


                <p>
                  Create your first category to organize your expenses.
                </p>


                <button
                  type="button"
                  onClick={handleAdd}
                  className="category-add-button"
                >

                  <Plus size={18} />

                  Create Category

                </button>

              </div>

            ) : (

              <div className="category-grid">

                {categories.map(
                  (category) => (

                    <div
                      key={
                        category._id
                      }
                      className="category-card"
                    >


                      {/* CARD HEADER */}

                      <div className="category-card-header">


                        <div className="category-card-info">

                          <div className="category-card-icon">

                            <Tags size={20} />

                          </div>


                          <div>

                            <h3>
                              {category.name}
                            </h3>

                            <span>
                              Expense Category
                            </span>

                          </div>

                        </div>


                        {/* ACTIONS */}

                        <div className="category-card-actions">

                          <button
                            type="button"
                            onClick={() =>
                              handleEdit(
                                category
                              )
                            }
                            title="Edit category"
                            className="category-edit-button"
                          >

                            <Pencil size={16} />

                          </button>


                          <button
                            type="button"
                            onClick={() =>
                              handleDelete(
                                category._id
                              )
                            }
                            title="Delete category"
                            className="category-delete-button"
                          >

                            <Trash2 size={16} />

                          </button>

                        </div>

                      </div>


                      {/* DESCRIPTION */}

                      <div className="category-description">

                        {category.description ||
                          "No description added."}

                      </div>


                      {/* FOOTER */}

                      <div className="category-card-footer">

                        <span>
                          Category
                        </span>

                        <span className="category-active">

                          Active

                        </span>

                      </div>

                    </div>

                  )
                )}

              </div>

            )}

          </div>

        </main>

      </div>

    </div>

  );

}


export default Categories;