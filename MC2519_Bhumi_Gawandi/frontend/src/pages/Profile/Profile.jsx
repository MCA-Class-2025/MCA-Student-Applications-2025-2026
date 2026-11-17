import { useEffect, useState } from "react";

import {
  User,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Lock,
  Edit3,
  Save,
  X,
} from "lucide-react";

import toast from "react-hot-toast";

import Sidebar from "../../components/dashboard/Sidebar";
import DashboardNavbar from "../../components/dashboard/DashboardNavbar";

import { getCurrentUser } from "../../services/authService";

import "./Profile.css";


function Profile() {

  const [user, setUser] = useState(null);

  const [loading, setLoading] = useState(true);

  const [editing, setEditing] = useState(false);

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
  });


  // ============================================================
  // GET USER NAME
  // ============================================================

  const getUserName = (data) => {

    return (
      data?.name ||
      data?.full_name ||
      data?.fullName ||
      data?.username ||
      data?.first_name ||
      data?.firstName ||
      ""
    );

  };


  // ============================================================
  // GET PHONE
  // ============================================================

  const getUserPhone = (data) => {

    return (
      data?.phone ||
      data?.contactNumber ||
      data?.contact_number ||
      data?.mobile ||
      ""
    );

  };


  // ============================================================
  // LOAD USER
  // ============================================================

  useEffect(() => {

    loadUser();

  }, []);


  const loadUser = async () => {

    try {

      setLoading(true);

      const token =
        localStorage.getItem("access_token") ||
        localStorage.getItem("token");


      if (!token) {

        toast.error("Please login again.");

        return;

      }


      const response =
        await getCurrentUser(token);


      console.log(
        "Profile API response:",
        response
      );


      /*
        Supports different backend responses:

        response.user

        response.data

        response
      */

      const userData =
        response?.user ||
        response?.data ||
        response;


      if (!userData) {

        throw new Error(
          "User data not found"
        );

      }


      setUser(userData);


      setFormData({

        name:
          getUserName(userData),

        email:
          userData?.email ||
          "",

        phone:
          getUserPhone(userData),

        address:
          userData?.address ||
          "",

      });


      // Save latest user locally

      localStorage.setItem(
        "user",
        JSON.stringify(userData)
      );


    } catch (error) {

      console.error(
        "Profile loading error:",
        error
      );


      // ========================================================
      // FALLBACK
      // ========================================================

      const storedUser =
        localStorage.getItem("user");


      if (storedUser) {

        try {

          const localUser =
            JSON.parse(storedUser);


          setUser(localUser);


          setFormData({

            name:
              getUserName(localUser),

            email:
              localUser?.email ||
              "",

            phone:
              getUserPhone(localUser),

            address:
              localUser?.address ||
              "",

          });

        } catch (parseError) {

          console.error(
            "User parse error:",
            parseError
          );

          toast.error(
            "Unable to load profile."
          );

        }

      } else {

        toast.error(
          "Unable to load profile."
        );

      }

    } finally {

      setLoading(false);

    }

  };


  // ============================================================
  // INPUT CHANGE
  // ============================================================

  const handleChange = (event) => {

    const {
      name,
      value,
    } = event.target;


    setFormData(
      (previous) => ({
        ...previous,
        [name]: value,
      })
    );

  };


  // ============================================================
  // EDIT PROFILE
  // ============================================================

  const handleEdit = () => {

    setEditing(true);

  };


  // ============================================================
  // CANCEL
  // ============================================================

  const handleCancel = () => {

    setFormData({

      name:
        getUserName(user),

      email:
        user?.email ||
        "",

      phone:
        getUserPhone(user),

      address:
        user?.address ||
        "",

    });


    setEditing(false);

  };


  // ============================================================
  // SAVE
  // ============================================================

  const handleSave = () => {

    if (!formData.name.trim()) {

      toast.error(
        "Name cannot be empty."
      );

      return;

    }


    const updatedUser = {

      ...user,

      name:
        formData.name.trim(),

      email:
        formData.email,

      phone:
        formData.phone.trim(),

      address:
        formData.address.trim(),

    };


    setUser(updatedUser);


    localStorage.setItem(
      "user",
      JSON.stringify(updatedUser)
    );


    setEditing(false);


    toast.success(
      "Profile updated successfully.",
      {
        duration: 2500,
        position: "top-right",
      }
    );

  };


  // ============================================================
  // DISPLAY VALUES
  // ============================================================

  const displayName =
    formData.name ||
    "User";


  const displayEmail =
    formData.email ||
    "No email available";


  const initial =
    displayName
      .trim()
      .charAt(0)
      .toUpperCase() ||
    "U";


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {

    return (

      <div className="profile-loading">

        <div className="profile-loading-spinner"></div>

        <p>
          Loading profile...
        </p>

      </div>

    );

  }


  // ============================================================
  // PAGE
  // ============================================================

  return (

    <div className="profile-layout">


      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="profile-sidebar">

        <Sidebar />

      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <div className="profile-main">


        {/* ====================================================
            NAVBAR
        ==================================================== */}

        <div className="profile-navbar-wrapper">

          <DashboardNavbar />

        </div>


        {/* ====================================================
            CONTENT
        ==================================================== */}

        <main className="profile-content">


          {/* ==================================================
              PAGE HEADER
          ================================================== */}

          <div className="profile-page-heading">

            <div className="profile-heading-label">

              <span className="profile-heading-dot"></span>

              ACCOUNT

            </div>


            <h1>
              My Profile
            </h1>


            <p>
              Manage your personal information and account details.
            </p>

          </div>


          {/* ==================================================
              PROFILE GRID
          ================================================== */}

          <div className="profile-container">


            {/* =================================================
                LEFT PROFILE CARD
            ================================================= */}

            <section className="profile-summary-card">


              <div className="profile-avatar">

                <span>
                  {initial}
                </span>

              </div>


              <h2>
                {displayName}
              </h2>


              <p className="profile-summary-email">
                {displayEmail}
              </p>


              <div className="profile-account-line">

                <User size={15} />

                <span>
                  SpendSmart Account
                </span>

              </div>


              <div className="profile-status">

                <span className="status-dot"></span>

                Active Account

              </div>


            </section>


            {/* =================================================
                RIGHT DETAILS CARD
            ================================================= */}

            <section className="profile-details-card">


              {/* =================================================
                  HEADER
              ================================================= */}

              <div className="profile-details-header">

                <div>

                  <div className="details-small-title">
                    ACCOUNT DETAILS
                  </div>

                  <h2>
                    Personal Information
                  </h2>

                  <p>
                    Your registered account information
                  </p>

                </div>


                {!editing && (

                  <button
                    type="button"
                    className="profile-edit-btn"
                    onClick={handleEdit}
                  >

                    <Edit3 size={15} />

                    Edit Profile

                  </button>

                )}

              </div>


              {/* =================================================
                  FORM
              ================================================= */}

              <div className="profile-form">


                {/* =================================================
                    NAME
                ================================================= */}

                <div className="profile-form-group">

                  <label>
                    Full Name
                  </label>

                  <div className="profile-input-wrapper">

                    <User size={17} />

                    <input
                      type="text"
                      name="name"
                      value={formData.name}
                      onChange={handleChange}
                      disabled={!editing}
                      placeholder="Enter your name"
                    />

                  </div>

                </div>


                {/* =================================================
                    EMAIL
                ================================================= */}

                <div className="profile-form-group">

                  <label>
                    Email Address
                  </label>

                  <div className="profile-input-wrapper">

                    <Mail size={17} />

                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      disabled
                      placeholder="Enter your email"
                    />

                  </div>

                  <small>
                    Email cannot be changed here.
                  </small>

                </div>


                {/* =================================================
                    PHONE
                ================================================= */}

                <div className="profile-form-group">

                  <label>
                    Phone Number
                  </label>

                  <div className="profile-input-wrapper">

                    <Phone size={17} />

                    <input
                      type="text"
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      disabled={!editing}
                      placeholder="Enter phone number"
                    />

                  </div>

                </div>


                {/* =================================================
                    ADDRESS
                ================================================= */}

                <div className="profile-form-group">

                  <label>
                    Address
                  </label>

                  <div className="profile-input-wrapper">

                    <MapPin size={17} />

                    <input
                      type="text"
                      name="address"
                      value={formData.address}
                      onChange={handleChange}
                      disabled={!editing}
                      placeholder="Enter address"
                    />

                  </div>

                </div>

              </div>


              {/* =================================================
                  ACCOUNT INFORMATION
              ================================================= */}

              <div className="account-section">

                <div className="account-section-heading">

                  <div>

                    <div className="details-small-title">
                      SECURITY
                    </div>

                    <h3>
                      Account Information
                    </h3>

                  </div>

                </div>


                <div className="account-grid">


                  {/* STATUS */}

                  <div className="account-item">

                    <div className="account-icon">

                      <Calendar size={17} />

                    </div>

                    <div>

                      <span>
                        Account Status
                      </span>

                      <strong>
                        Active
                      </strong>

                    </div>

                  </div>


                  {/* PASSWORD */}

                  <div className="account-item">

                    <div className="account-icon">

                      <Lock size={17} />

                    </div>

                    <div>

                      <span>
                        Password
                      </span>

                      <strong>
                        Protected
                      </strong>

                    </div>

                  </div>


                </div>

              </div>


              {/* =================================================
                  ACTIONS
              ================================================= */}

              {editing && (

                <div className="profile-actions">

                  <button
                    type="button"
                    className="profile-cancel-btn"
                    onClick={handleCancel}
                  >

                    <X size={15} />

                    Cancel

                  </button>


                  <button
                    type="button"
                    className="profile-save-btn"
                    onClick={handleSave}
                  >

                    <Save size={15} />

                    Save Changes

                  </button>

                </div>

              )}

            </section>

          </div>

        </main>

      </div>

    </div>

  );

}


export default Profile;