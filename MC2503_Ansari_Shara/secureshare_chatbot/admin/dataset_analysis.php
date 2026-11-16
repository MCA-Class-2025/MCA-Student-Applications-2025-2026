<?php

include("admin_auth.php");
include("admin_navbar.php");

// ==========================
// Dataset Statistics
// ==========================

// Total Records
$total = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total FROM cybersecurity_dataset"));

// Blocked Records
$blocked = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total FROM cybersecurity_dataset
WHERE blocked = 1"));

// Suspicious Activity
$suspicious = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total FROM cybersecurity_dataset
WHERE suspicious_activity = 1"));

// Average Failed Attempts
$failed = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT AVG(failed_attempts) AS avg_failed
FROM cybersecurity_dataset"));

// High Privilege Users (4 & 5)
$privilege = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE privilege_level >= 4"));

// ==========================
// Account Status
// ==========================

$active = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE account_status='Active'"));

$suspended = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE account_status='Suspended'"));

$locked = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE account_status='Locked'"));

// ==========================
// Roles
// ==========================

$admins = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE role='Admin'"));

$users = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE role='User'"));

$guests = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE role='Guest'"));

// ==========================
// Login Success / Failure
// ==========================

$success = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE success = 1"));

$failure = mysqli_fetch_assoc(mysqli_query($conn,
"SELECT COUNT(*) AS total
FROM cybersecurity_dataset
WHERE success = 0"));

?>

<!DOCTYPE html>
<html>

<head>

    <title>Dataset Analysis</title>

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

</head>

<body>

<div class="container mt-4">

<h2 class="mb-4">Cybersecurity Dataset Analysis</h2>

<div class="row">

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Total Records</h6>
<h3><?= $total['total']; ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Blocked Records</h6>
<h3><?= $blocked['total']; ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Suspicious Activity</h6>
<h3><?= $suspicious['total']; ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Average Failed Attempts</h6>
<h3><?= round($failed['avg_failed'],2); ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>High Privilege Users</h6>
<h3><?= $privilege['total']; ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Active Accounts</h6>
<h3><?= $active['total']; ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Suspended Accounts</h6>
<h3><?= $suspended['total']; ?></h3>
</div>
</div>
</div>

<div class="col-md-3 mb-3">
<div class="card shadow-sm">
<div class="card-body text-center">
<h6>Locked Accounts</h6>
<h3><?= $locked['total']; ?></h3>
</div>
</div>
</div>

</div>

<hr>

<h4 class="mt-4">User Roles</h4>

<table class="table table-bordered mt-3">

<tr>
<th>Role</th>
<th>Total</th>
</tr>

<tr>
<td>Admin</td>
<td><?= $admins['total']; ?></td>
</tr>

<tr>
<td>User</td>
<td><?= $users['total']; ?></td>
</tr>

<tr>
<td>Guest</td>
<td><?= $guests['total']; ?></td>
</tr>

</table>

<h4 class="mt-4">Login Statistics</h4>

<table class="table table-bordered mt-3">

<tr>
<th>Status</th>
<th>Total</th>
</tr>

<tr>
<td>Successful Logins</td>
<td><?= $success['total']; ?></td>
</tr>

<tr>
<td>Failed Logins</td>
<td><?= $failure['total']; ?></td>
</tr>

</table>

</div>

</body>

</html>