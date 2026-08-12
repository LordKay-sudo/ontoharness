package dev.ontoharness.spring.example;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assumptions.assumeTrue;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

import org.junit.jupiter.api.Test;

class BasicUsageExampleTest {

    @Test
    void runsAgainstLocalSidecarWhenAvailable() throws Exception {
        assumeTrue(sidecarHealthy("http://localhost:8010"), "OntoHarness sidecar not running on :8010");

        var lines = BasicUsageExample.run("http://localhost:8010");

        assertThat(lines).hasSize(3);
        assertThat(lines.get(0)).isEqualTo("Valid scenario conforms=true");
        assertThat(lines.get(1)).isEqualTo("Fabricated scenario blocked=true");
        assertThat(lines.get(2)).contains("Repair hints=");
    }

    private static boolean sidecarHealthy(String baseUrl) {
        try {
            HttpResponse<String> response = HttpClient.newHttpClient()
                    .send(
                            HttpRequest.newBuilder(URI.create(baseUrl + "/health")).GET().build(),
                            HttpResponse.BodyHandlers.ofString());
            return response.statusCode() == 200;
        } catch (Exception e) {
            return false;
        }
    }
}
