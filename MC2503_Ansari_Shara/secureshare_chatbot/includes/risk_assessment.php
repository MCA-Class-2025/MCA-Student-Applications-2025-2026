<?php

function calculateRisk(
    $failed_attempts,
    $suspicious_activity,
    $privilege_level,
    $session_duration,
    $blocked
)
{
    $risk_score = 0;

    // Failed Attempts
    if($failed_attempts >= 5)
    {
        $risk_score += 30;
    }

    // Suspicious Activity
    if($suspicious_activity == 1)
    {
        $risk_score += 40;
    }

    // High Privilege User
    if($privilege_level == "High")
    {
        $risk_score += 10;
    }

    // Long Session
    if($session_duration > 480)
    {
        $risk_score += 10;
    }

    // Blocked User
    if($blocked == 1)
    {
        $risk_score += 30;
    }

    // Maximum Score = 100
    if($risk_score > 100)
    {
        $risk_score = 100;
    }

    // Risk Level
    if($risk_score >= 70)
    {
        $threat_level = "High";
        $decision = "Deny";
    }
    elseif($risk_score >= 30)
    {
        $threat_level = "Medium";
        $decision = "Allow";
    }
    else
    {
        $threat_level = "Low";
        $decision = "Allow";
    }

    return [
        "risk_score" => $risk_score,
        "threat_level" => $threat_level,
        "decision" => $decision
    ];
}

?>