<?php
if(session_status() == PHP_SESSION_NONE)
{
    session_start();
}
require_once("../config/db.php");
$admin_name = $_SESSION['username'];

$admin_id = $_SESSION['user_id'];

$notification_sql = "SELECT *
                     FROM notifications
                     WHERE user_id='$admin_id'
                     AND status='Unread'";

$notification_result = mysqli_query($conn,$notification_sql);

$notification_count = mysqli_num_rows($notification_result);

?>

<style>

*{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:'Segoe UI',sans-serif;
}

.navbar{

    width:100%;
    background:#ffffff;
    box-shadow:0 2px 10px rgba(0,0,0,.08);
    padding:18px 40px;

    display:flex;
    justify-content:space-between;
    align-items:center;

}

.logo{

    display:flex;
    align-items:center;
    gap:15px;

}

.logo img{

    width:48px;
    height:48px;
    object-fit:contain;

}

.logo h2{

    color:#2563eb;
    font-size:26px;
    font-weight:700;

}

.right{

    display:flex;
    align-items:center;
    gap:15px;

}

.notification{

    position:relative;
    text-decoration:none;
    color:#f59e0b;
    font-size:34px;

    display:flex;
    align-items:center;
    margin-right:8px;

}

.badge{

    position:absolute;

    top:-6px;
    right:-8px;

    background:red;
    color:white;

    width:20px;
    height:20px;

    border-radius:50%;

    display:flex;
    justify-content:center;
    align-items:center;

    font-size:12px;
    font-weight:bold;

}

.account{

    background:#2563eb;
    color:white;
    text-decoration:none;

    padding:11px 22px;
    border-radius:10px;

    display:flex;
    align-items:center;
    gap:8px;

    transition:.3s;

}

.account:hover{

    background:#1d4ed8;

}

.logout{

    background:#ef4444;
    color:white;
    text-decoration:none;

    padding:11px 22px;
    border-radius:10px;

    transition:.3s;

}

.logout:hover{

    background:#dc2626;

}

</style>

<div class="navbar">

    <div class="logo">

        <img src="../assets/images/logo.png">

        <h2>SecureShare</h2>

    </div>

<div class="right">

    <a href="../dashboard/notifications.php"
       class="notification">

        <i class="bi bi-bell-fill"></i>

        <?php
        if($notification_count > 0)
        {
        ?>

        <span class="badge">

            <?php echo $notification_count; ?>

        </span>

        <?php
        }
        ?>

    </a>

    <a href="account.php"
       class="account">

        <i class="bi bi-person-circle"></i>

        Account

    </a>

    <a href="../auth/logout.php"
       class="logout">

        <i class="bi bi-box-arrow-right"></i>

        Logout

    </a>

</div>

</div>