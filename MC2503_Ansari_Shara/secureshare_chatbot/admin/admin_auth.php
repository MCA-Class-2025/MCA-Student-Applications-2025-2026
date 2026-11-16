<?php

if (session_status() == PHP_SESSION_NONE)
{
    session_start();
}

if(!isset($_SESSION['user_id']))
{
    header("Location: ../auth/login.php");
    exit();
}

if($_SESSION['role'] != "admin")
{
    die("Access Denied!");
}

include("../config/db.php");

?>