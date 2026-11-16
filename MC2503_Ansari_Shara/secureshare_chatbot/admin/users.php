<?php
session_start();
require_once("../config/db.php");
include("admin_auth.php");

$admin_id = $_SESSION['user_id'];

$sql = "SELECT *
        FROM users
        ORDER BY created_at DESC";

$result = mysqli_query($conn, $sql);
?>

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width, initial-scale=1.0">

<title>Users | SecureShare</title>

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

    max-width:1200px;
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

.status-active{

    color:green;
    font-weight:bold;

}

.status-blocked{

    color:red;
    font-weight:bold;

}

.block-btn{

    background:#ef4444;
    color:white;
    text-decoration:none;
    padding:8px 14px;
    border-radius:8px;

}

.unblock-btn{

    background:#22c55e;
    color:white;
    text-decoration:none;
    padding:8px 14px;
    border-radius:8px;

}

.admin-tag{

    color:#2563eb;
    font-weight:bold;

}

</style>

</head>

<body>

<?php include("admin_navbar.php"); ?>

<div class="container">

<div class="heading">

<h2>

Manage Users

</h2>

<p>

View, Block and Unblock Registered Users

</p>

<div class="quick-actions">

<a href="dashboard.php" class="action-btn">

Dashboard

</a>

<a href="audit_logs.php" class="action-btn">

Audit Logs

</a>

<a href="risk_reports.php" class="action-btn">

Risk Reports

</a>

</div>

</div>

<div class="table-box">

<table>

<tr>

<th>Username</th>

<th>Email</th>

<th>Role</th>

<th>Status</th>

<th>Created</th>

<th>Action</th>

</tr>

<?php

while($row = mysqli_fetch_assoc($result))
{

?>
<tr>

<td>

<?php echo htmlspecialchars($row['username']); ?>

</td>

<td>

<?php echo htmlspecialchars($row['email']); ?>

</td>

<td>

<?php

if($row['role'] == "admin")
{
    echo "<span class='admin-tag'>Admin</span>";
}
else
{
    echo "User";
}

?>

</td>

<td>

<?php

if($row['account_status'] == "Active")
{
?>

<span class="status-active">

Active

</span>

<?php
}
else
{
?>

<span class="status-blocked">

Blocked

</span>

<?php
}
?>

</td>

<td>

<?php

echo date(
"d M Y",
strtotime($row['created_at'])
);

?>

</td>

<td>

<?php

if($row['role'] == "admin")
{
?>

-

<?php
}
elseif($row['account_status'] == "Active")
{
?>

<a
href="block_user.php?id=<?php echo $row['user_id']; ?>"
class="block-btn"
onclick="return confirm('Block this user?')">

Block

</a>

<?php
}
else
{
?>

<a
href="unblock_user.php?id=<?php echo $row['user_id']; ?>"
class="unblock-btn"
onclick="return confirm('Unblock this user?')">

Unblock

</a>

<?php
}
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