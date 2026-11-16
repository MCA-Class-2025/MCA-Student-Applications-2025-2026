<?php

if(session_status() == PHP_SESSION_NONE)
{
    session_start();
}

require_once("../config/db.php");

$notification_count = 0;

if(isset($_SESSION['user_id']))
{
    $user_id = $_SESSION['user_id'];

    $notification_sql = "SELECT COUNT(*) AS total
                         FROM notifications
                         WHERE user_id='$user_id'
                         AND status='Unread'";

    $notification_result =
    mysqli_query($conn, $notification_sql);

    $notification_data =
    mysqli_fetch_assoc($notification_result);

    $notification_count =
    $notification_data['total'];
}
?>

<div class="navbar">

    <div class="logo-section">

        <a href="../dashboard/user_dashboard.php">

            <img src="../assets/images/logo.png"
                 alt="SecureShare Logo"
                 class="logo-img">

        </a>

        <a href="../dashboard/user_dashboard.php"
           class="logo-link">

            <h2 class="logo-text">
                SecureShare
            </h2>

        </a>

    </div>

    <div class="nav-actions">

        <a href="../dashboard/notifications.php"
        class="notification-btn">
        
        <i class="bi bi-bell-fill"></i>
        <?php
        if($notification_count > 0)
            {
        ?>
        <span class="notification-badge"></span>
        <?php
        }
        ?>
        </a>

        <a href="../dashboard/account.php"
           class="account-btn">

            <i class="bi bi-person-circle"></i>

            Account

        </a>

        <a href="../auth/logout.php"
           class="logout-btn">

            Logout

        </a>

    </div>

</div>