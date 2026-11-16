<?php
session_start();
require_once("../config/db.php");
include("admin_auth.php");

$admin_name = $_SESSION['username'];

/* ===========================
   Dashboard Statistics
=========================== */

// Total Users
$user_sql = "SELECT COUNT(*) AS total_users
             FROM users
             WHERE role='user'";

$user_result = mysqli_query($conn,$user_sql);
$user_data = mysqli_fetch_assoc($user_result);
$total_users = $user_data['total_users'];


// Total Files
$file_sql = "SELECT COUNT(*) AS total_files
             FROM files";

$file_result = mysqli_query($conn,$file_sql);
$file_data = mysqli_fetch_assoc($file_result);
$total_files = $file_data['total_files'];


// Blocked Users
$blocked_sql = "SELECT COUNT(*) AS blocked_users
                FROM users
                WHERE account_status='Blocked'";

$blocked_result = mysqli_query($conn,$blocked_sql);
$blocked_data = mysqli_fetch_assoc($blocked_result);
$blocked_users = $blocked_data['blocked_users'];


// High Risk Activities
$risk_sql = "SELECT COUNT(*) AS high_risk
             FROM audit_logs
             WHERE risk_score >= 70";

$risk_result = mysqli_query($conn,$risk_sql);
$risk_data = mysqli_fetch_assoc($risk_result);
$high_risk = $risk_data['high_risk'];


// Recent Activities
$activity_sql = "SELECT audit_logs.activity,
                        audit_logs.timestamp,
                        users.username
                 FROM audit_logs
                 JOIN users
                 ON audit_logs.user_id = users.user_id
                 ORDER BY audit_logs.timestamp DESC
                 LIMIT 8";

$activity_result = mysqli_query($conn,$activity_sql);

?>

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Admin Dashboard | SecureShare</title>

<link rel="stylesheet"
href="../assets/css/navbar.css">

<link rel="stylesheet"
href="../assets/css/ai_chatbot.css">

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
    margin:0;
    padding:0;
    background:#f4f7fc;
}

/* Container */

.container{

    max-width:1200px;
    margin:40px auto;
    padding:0 20px;

}

/* Welcome */

.welcome-card{

    background:white;
    padding:30px;
    border-radius:20px;
    box-shadow:0 5px 20px rgba(0,0,0,.08);
    margin-bottom:30px;

}

.welcome-card h2{

    color:#111827;
    margin-bottom:10px;

}

.welcome-card p{

    color:#6b7280;

}

/* Buttons */

.quick-actions{

    display:flex;
    gap:15px;
    margin-top:25px;
    flex-wrap:wrap;

}

.action-btn{

    text-decoration:none;
    background:#2563eb;
    color:white;
    padding:12px 20px;
    border-radius:10px;
    transition:.3s;

}

.action-btn:hover{

    background:#1d4ed8;

}

/* Cards */

.stats{

    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(250px,1fr));
    gap:20px;
    margin-bottom:30px;

}

.card{

    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0 5px 20px rgba(0,0,0,.08);

}

.card h3{

    color:#6b7280;
    font-size:16px;

}

.number{

    font-size:36px;
    font-weight:bold;
    color:#2563eb;
    margin-top:10px;

}

/* Activity */

.section{

    background:white;
    padding:25px;
    border-radius:20px;
    box-shadow:0 5px 20px rgba(0,0,0,.08);

}

.section h3{

    margin-bottom:20px;

}

.activity{

    padding:18px 0;
    border-bottom:1px solid #e5e7eb;

}

.activity:last-child{

    border-bottom:none;

}

.activity-title{

    font-size:16px;
    font-weight:600;
    color:#111827;

}

.activity-time{

    margin-top:6px;
    color:#6b7280;
    font-size:14px;

}

.username{

    color:#2563eb;
    font-weight:bold;

}

</style>

</head>

<body>

<?php include("admin_navbar.php"); ?>

<div class="container">

<div class="welcome-card">

<h2>

Welcome,
<?php echo htmlspecialchars($admin_name); ?>

</h2>

<p>

SecureShare Administrator Dashboard

</p>

<div class="quick-actions">

<a href="users.php"
class="action-btn">

Users

</a>

<a href="audit_logs.php"
class="action-btn">

Audit Logs

</a>

<a href="risk_reports.php"
class="action-btn">

Risk Reports

</a>

</div>

</div>

<div class="stats">

<div class="card">

<h3>Total Users</h3>

<div class="number">

<?php echo $total_users; ?>

</div>

</div>

<div class="card">

<h3>Total Files</h3>

<div class="number">

<?php echo $total_files; ?>

</div>

</div>

<div class="card">

<h3>Blocked Users</h3>

<div class="number">

<?php echo $blocked_users; ?>

</div>

</div>

<div class="card">

<h3>High Risk Cases</h3>

<div class="number">

<?php echo $high_risk; ?>

</div>

</div>

</div>

<div class="section">

<h3>

<i class="bi bi-clock-history"></i>

Recent Activity

</h3>
<?php
if(mysqli_num_rows($activity_result) > 0)
{
    while($activity = mysqli_fetch_assoc($activity_result))
    {
?>

<div class="activity">

<?php

$text = $activity['activity'];

$text = str_replace("Uploaded file: ", 'Uploaded "', $text);
$text = str_replace("Deleted file: ", 'Deleted "', $text);
$text = str_replace("Downloaded file: ", 'Downloaded "', $text);
$text = str_replace("Viewed file: ", 'Viewed "', $text);
$text = str_replace("Changed permission of file: ", 'Changed permission for "', $text);
$text = str_replace("Unshared file: ", 'Unshared "', $text);

if(strpos($text,"Shared file: ")===0)
{
    $text = str_replace("Shared file: ",'Shared "',$text);
    $text = str_replace(" with ",'" with ',$text);
}

if(
    strpos($activity['activity'],"Uploaded file:")===0 ||
    strpos($activity['activity'],"Deleted file:")===0 ||
    strpos($activity['activity'],"Downloaded file:")===0 ||
    strpos($activity['activity'],"Viewed file:")===0 ||
    strpos($activity['activity'],"Changed permission of file:")===0 ||
    strpos($activity['activity'],"Unshared file:")===0
)
{
    $text .= '"';
}

?>

<div class="activity-title">

<span class="username">

<?php
echo htmlspecialchars($activity['username']);
?>

</span>

-

<?php
echo htmlspecialchars($text);
?>

</div>

<div class="activity-time">

<?php

echo date(
"d M Y • h:i A",
strtotime($activity['timestamp'])
);

?>

</div>

</div>

<?php
    }
}
else
{
?>

<div class="activity">

No recent activity found.

</div>

<?php
}
?>

</div>

</div>

<!-- ==========================================
     AI SECURITY ASSISTANT
========================================== -->

<button id="aiButton">

    <img src="../assets/images/logo.png" alt="AI Assistant">

</button>


<div id="chatWindow">

    <!-- Header -->

    <div class="chat-header">

        <div class="chat-title">

            <img
            src="../assets/images/logo.png"
            alt="SecureShare">

            <h3>AI Security Assistant</h3>

        </div>

        <div class="chat-actions">

            <button id="minimizeChat">

                <i class="bi bi-dash-lg"></i>

            </button>

            <button id="closeChat">

                <i class="bi bi-x-lg"></i>

            </button>

        </div>

    </div>


    <!-- Chat Body -->

    <div class="chat-body" id="chatBody">

        <!-- Messages will appear here -->

    </div>


    <!-- Footer -->

    <div class="chat-footer">

        <input
        type="text"
        id="chatInput"
        placeholder="Ask something...">

        <button id="sendBtn">

            <i class="bi bi-send-fill"></i>

        </button>

    </div>

</div>

<script src="../assets/js/ai_chatbot.js"></script>

</body>

</html>