package com.openapi.weather_project.Controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/ai")
@CrossOrigin(origins = "*")
public class AIController {

    private final RestTemplate restTemplate = new RestTemplate();

    private final String AI_SERVICE_URL =
            "http://localhost:8000/ask";

    @PostMapping("/ask")
    public ResponseEntity<?> askAI(
            @RequestBody Map<String, String> request) {

        String question = request.get("question");

        if (question == null || question.trim().isEmpty()) {

            return ResponseEntity.badRequest().body(
                    Map.of(
                            "error",
                            "Question cannot be empty"
                    )
            );
        }

        Map<String, String> aiRequest = Map.of(
                "question",
                question
        );

        ResponseEntity<Map> response =
                restTemplate.postForEntity(
                        AI_SERVICE_URL,
                        aiRequest,
                        Map.class
                );

        return ResponseEntity.ok(
                response.getBody()
        );
    }
}
