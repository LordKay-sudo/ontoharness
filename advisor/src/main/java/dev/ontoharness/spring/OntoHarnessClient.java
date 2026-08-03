package dev.ontoharness.spring;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Objects;

/**
 * Client for the OntoHarness Python validation sidecar.
 * v0.1 skeleton — wire into a Spring AI {@code CallAdvisor} in 0.4.
 */
public final class OntoHarnessClient {

    private final URI baseUrl;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;

    public OntoHarnessClient(String baseUrl) {
        this(URI.create(baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl));
    }

    public OntoHarnessClient(URI baseUrl) {
        this.baseUrl = Objects.requireNonNull(baseUrl, "baseUrl");
        this.httpClient = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
        this.objectMapper = new ObjectMapper();
    }

    public ValidationResponse validate(String domain, String turtle) {
        try {
            String body = objectMapper.writeValueAsString(
                    new ValidateRequest(domain, "turtle", turtle));
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(baseUrl.resolve("/api/v1/validate"))
                    .timeout(Duration.ofSeconds(30))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() >= 400) {
                throw new OntoHarnessException("Validation request failed: HTTP " + response.statusCode()
                        + " — " + response.body());
            }
            JsonNode json = objectMapper.readTree(response.body());
            return new ValidationResponse(
                    json.path("domain").asText(domain),
                    json.path("conforms").asBoolean(false),
                    readHints(json.path("repair_hints")));
        } catch (OntoHarnessException e) {
            throw e;
        } catch (Exception e) {
            throw new OntoHarnessException("Failed to call OntoHarness sidecar", e);
        }
    }

    private List<String> readHints(JsonNode node) {
        if (!node.isArray()) {
            return List.of();
        }
        return objectMapper.convertValue(
                node,
                objectMapper.getTypeFactory().constructCollectionType(List.class, String.class));
    }

    private record ValidateRequest(String domain, String format, String content) {}

    public record ValidationResponse(String domain, boolean conforms, List<String> repairHints) {}

    public static final class OntoHarnessException extends RuntimeException {
        public OntoHarnessException(String message) {
            super(message);
        }

        public OntoHarnessException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}
