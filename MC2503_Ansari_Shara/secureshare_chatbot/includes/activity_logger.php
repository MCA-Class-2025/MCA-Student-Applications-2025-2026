<?php

function logActivity($conn, $user_id, $activity, $risk_score = 0, $decision = "Allow")
{
    $activity = mysqli_real_escape_string($conn, $activity);
    $decision = mysqli_real_escape_string($conn, $decision);

    $sql = "INSERT INTO audit_logs
            (user_id, activity, risk_score, decision)
            VALUES
            (
                '$user_id',
                '$activity',
                '$risk_score',
                '$decision'
            )";

    if(!mysqli_query($conn, $sql))
    {
        die("Audit Log Error: " . mysqli_error($conn));
    }

    return true;
}

?>