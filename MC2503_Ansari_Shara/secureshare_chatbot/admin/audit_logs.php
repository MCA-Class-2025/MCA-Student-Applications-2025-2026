<?php
session_start();
require_once("../config/db.php");
include("admin_auth.php");

$sql = "SELECT audit_logs.*,
               users.username
        FROM audit_logs
        LEFT JOIN users
        ON audit_logs.user_id = users.user_id
        ORDER BY audit_logs.timestamp DESC";

$result = mysqli_query($conn,$sql);
?>

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Audit Logs | SecureShare</title>

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
max-width:1300px;
margin:40px auto;
padding:0 20px;
}

.heading{
background:white;
padding:30px;
border-radius:20px;
box-shadow:0 5px 20px rgba(0,0,0,.08);
margin-bottom:30px;
}

.heading h2{
color:#111827;
margin-bottom:10px;
}

.heading p{
color:#6b7280;
}

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

.table-box{
background:white;
padding:25px;
border-radius:20px;
box-shadow:0 5px 20px rgba(0,0,0,.08);
overflow-x:auto;
}

table{
width:100%;
border-collapse:collapse;
}

th{
background:#2563eb;
color:white;
padding:15px;
text-align:left;
}

td{
padding:15px;
border-bottom:1px solid #e5e7eb;
}

tr:hover{
background:#f9fafb;
}

.allowed{
color:green;
font-weight:bold;
}

.denied{
color:red;
font-weight:bold;
}

</style>

</head>

<body>

<?php include("admin_navbar.php"); ?>

<div class="container">

<div class="heading">

<h2>

Audit Logs

</h2>

<p>

View all user activities performed inside SecureShare.

</p>

<div class="quick-actions">

<a href="dashboard.php" class="action-btn">
Dashboard
</a>

<a href="users.php" class="action-btn">
Users
</a>

<a href="risk_reports.php" class="action-btn">
Risk Reports
</a>

</div>

</div>

<div class="table-box">

<table>

<tr>

<th>User</th>
<th>Activity</th>
<th>Risk Score</th>
<th>Decision</th>
<th>Date & Time</th>

</tr>

<?php

while($row=mysqli_fetch_assoc($result))
{

?>
<tr>

<td>

<?php

if($row['username'])
{
    echo htmlspecialchars($row['username']);
}
else
{
    echo "Unknown User";
}

?>

</td>

<td>

<?php echo htmlspecialchars($row['activity']); ?>

</td>

<td>

<?php echo $row['risk_score']; ?>

</td>

<td>

<?php

$class = ($row['decision'] == "Allow") ? "allowed" : "denied";

?>

<span class="<?php echo $class; ?>">

<?php echo htmlspecialchars($row['decision']); ?>

</span>

</td>

<td>

<?php

echo date(
"d M Y • h:i A",
strtotime($row['timestamp'])
);

?>

</td>

</tr>

<?php

}

?>

</table>

</div>

</div>

</body>

</html>