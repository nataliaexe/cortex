package dev.julianasilva.portfolio.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/about")
public class AboutController {

    @GetMapping
    public Map<String, Object> getAbout() {
        return Map.of(
            "name", "Natalia",
            "bio", "Full Stack Java Developer building modern web applications.",
            "stack", List.of("Java 17", "Spring Boot", "PostgreSQL", "React", "Docker")
        );
    }
}
