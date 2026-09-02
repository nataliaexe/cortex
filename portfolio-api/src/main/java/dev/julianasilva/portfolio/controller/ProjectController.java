package dev.julianasilva.portfolio.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/projects")
public class ProjectController {

    @GetMapping
    public List<Map<String, Object>> listProjects() {
        return List.of(
            Map.of("id", 1, "title", "Neural Command Center", "description", "Signal monitoring dashboard", "techStack", List.of("Java", "Spring", "React")),
            Map.of("id", 2, "title", "API Gateway Studio", "description", "Secure service gateway", "techStack", List.of("Spring Boot", "JWT", "Postgres"))
        );
    }

    @GetMapping("/{id}")
    public Map<String, Object> getProject(@PathVariable Long id) {
        return Map.of("id", id, "title", "Sample Project", "description", "Portfolio sample", "techStack", List.of("Java", "Spring"));
    }
}
