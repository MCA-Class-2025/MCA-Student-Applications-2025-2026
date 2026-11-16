<?php

header("Content-Type: application/json");

// ------------------------------------------
// Check Request
// ------------------------------------------

if ($_SERVER["REQUEST_METHOD"] !== "POST") {

    echo json_encode([
        "status" => "error",
        "message" => "Invalid request."
    ]);

    exit;
}

// ------------------------------------------
// Read Question
// ------------------------------------------

$question = trim($_POST["question"] ?? "");

if ($question == "") {

    echo json_encode([
        "status" => "error",
        "message" => "Question cannot be empty."
    ]);

    exit;
}

// ------------------------------------------
// Send Request to Flask
// ------------------------------------------

$data = json_encode([
    "question" => $question
]);

$ch = curl_init("http://127.0.0.1:5000/chat");

curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    "Content-Type: application/json"
]);
curl_setopt($ch, CURLOPT_POSTFIELDS, $data);

$response = curl_exec($ch);

if (curl_errno($ch)) {

    echo json_encode([
        "status" => "error",
        "message" => curl_error($ch)
    ]);

    curl_close($ch);
    exit;
}

curl_close($ch);

// ------------------------------------------
// Return Flask Response
// ------------------------------------------

echo $response;