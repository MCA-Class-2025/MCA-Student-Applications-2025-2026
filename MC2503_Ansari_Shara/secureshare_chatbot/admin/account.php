<?php
session_start();
require_once("../config/db.php");
include("admin_auth.php");

$admin_id = $_SESSION['user_id'];

$sql = "SELECT *
        FROM users
        WHERE user_id = '$admin_id'";

$result = mysqli_query($conn,$sql);

$admin = mysqli_fetch_assoc($result);
?>

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Account | SecureShare</title>

<link rel="stylesheet"
href="../assets/css/navbar.css">

<link rel="stylesheet"
href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">

<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:'Segoe UI',sans-serif;
}

body{
    background:#f4f7fc;
}

.container{

    max-width:900px;
    margin:40px auto;
    padding:0 20px;

}

.card{

    background:white;
    border-radius:20px;
    box-shadow:0 5px 20px rgba(0,0,0,.08);
    padding:35px;

}

.card h2{

    color:#111827;
    margin-bottom:10px;

}

.card p{

    color:#6b7280;
    margin-bottom:30px;

}

.info{

    display:flex;
    justify-content:space-between;
    align-items:center;

    padding:18px 0;

    border-bottom:1px solid #e5e7eb;

}

.label{

    font-weight:600;
    color:#374151;

}

.value{

    color:#111827;

}

.role{

    color:#2563eb;
    font-weight:bold;

}

.buttons{

    display:flex;
    gap:15px;
    margin-top:35px;
    flex-wrap:wrap;

}

.btn{

    text-decoration:none;
    color:white;
    background:#2563eb;

    padding:12px 20px;

    border-radius:10px;

    transition:.3s;

}

.btn:hover{

    background:#1d4ed8;

}

</style>

</head>

<body>

<?php include("admin_navbar.php"); ?>

<div class="container">

<div class="card">

<h2>

My Account

</h2>

<p>

Manage your administrator account information.

</p>

<div class="info">

<div class="label">

Username

</div>

<div class="value">

<?php echo htmlspecialchars($admin['username']); ?>

</div>

</div>

<div class="info">

<div class="label">

Email

</div>

<div class="value">

<?php echo htmlspecialchars($admin['email']); ?>

</div>

</div>

<div class="info">

<div class="label">

Role

</div>

<div class="value role">

Administrator

</div>

</div>
<div class="info">

<div class="label">

Account Status

</div>

<div class="value">

<?php echo htmlspecialchars($admin['account_status']); ?>

</div>

</div>

<div class="info">

<div class="label">

Created On

</div>

<div class="value">

<?php

echo date(
"d M Y",
strtotime($admin['created_at'])
);

?>

</div>

</div>

<div class="buttons">

<a href="../auth/change_password.php"
class="btn">

<i class="bi bi-key-fill"></i>

Change Password

</a>

<a href="dashboard.php"
class="btn">

<i class="bi bi-speedometer2"></i>

Back to Dashboard

</a>

</div>

</div>

</div>

</body>

</html>