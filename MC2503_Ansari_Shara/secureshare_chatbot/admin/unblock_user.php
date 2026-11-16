<?php

session_start();
require_once("../config/db.php");
include("admin_auth.php");

if(!isset($_GET['id']))
{
    header("Location: users.php");
    exit();
}

$user_id = $_GET['id'];

// Don't allow changing another admin
$check_sql = "SELECT role
              FROM users
              WHERE user_id='$user_id'";

$check_result = mysqli_query($conn,$check_sql);
$user = mysqli_fetch_assoc($check_result);

if($user['role'] == "admin")
{
    header("Location: users.php");
    exit();
}

// Unblock user
$sql = "UPDATE users
        SET account_status='Active'
        WHERE user_id='$user_id'";

mysqli_query($conn,$sql);

// Log activity
$admin_id = $_SESSION['user_id'];

$log_sql = "INSERT INTO audit_logs
(user_id,activity,risk_score,decision)
VALUES
('$admin_id',
'Unblocked user ID: $user_id',
0,
'Allowed')";

mysqli_query($conn,$log_sql);

header("Location: users.php");
exit();

?>