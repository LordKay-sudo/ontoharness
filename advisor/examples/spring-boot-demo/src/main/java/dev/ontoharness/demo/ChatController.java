package dev.ontoharness.demo;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import dev.ontoharness.spring.OntologyValidationAdvisor;

@RestController
@RequestMapping("/chat")
public class ChatController {

    private final ChatClient chatClient;

    public ChatController(ChatClient chatClient) {
        this.chatClient = chatClient;
    }

    public record ChatRequest(String scenario) {}

    @GetMapping
    public Map<String, Object> help() {
        return Map.of(
                "message",
                "POST /chat with {\"scenario\":\"valid\"} or {\"scenario\":\"fabricated\"}. Requires OntoHarness on :8010.",
                "scenarios",
                List.of("valid", "fabricated"));
    }

    @PostMapping
    public Map<String, Object> chat(@RequestBody ChatRequest request) {
        String scenario = request.scenario() == null ? "valid" : request.scenario().trim().toLowerCase();
        if (!scenario.equals("valid") && !scenario.equals("fabricated")) {
            throw new ResponseStatusException(
                    HttpStatus.BAD_REQUEST, "scenario must be 'valid' or 'fabricated'");
        }

        ChatClientResponse response =
                chatClient.prompt().user("scenario:" + scenario).call().chatClientResponse();

        Map<String, Object> body = new LinkedHashMap<>();
        body.put("scenario", scenario);
        body.put("text", response.chatResponse().getResult().getOutput().getText());

        Object conforms = response.context().get(OntologyValidationAdvisor.CONTEXT_ONTOLOGY_CONFORMS);
        if (conforms != null) {
            body.put("conforms", conforms);
        } else {
            body.put("conforms", true);
        }

        Object hints = response.context().get(OntologyValidationAdvisor.CONTEXT_ONTOLOGY_HINTS);
        if (hints instanceof List<?> hintList && !hintList.isEmpty()) {
            body.put("repair_hints", hintList);
        }

        return body;
    }
}
