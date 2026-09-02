package dev.julianasilva.portfolio.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/contact")
public class ContactController {

    @PostMapping
    public ResponseEntity<Map<String, String>> createContact(@RequestBody Map<String, String> payload) {
        return ResponseEntity.ok(Map.of("status", "received", "message", "Thanks for contacting Natalia."));
    }
}
