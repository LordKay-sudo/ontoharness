package dev.ontoharness.spring.example;

import java.util.List;
import java.util.Map;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;

import dev.ontoharness.spring.OntologyValidationAdvisor;
import dev.ontoharness.spring.OntologyValidationPolicy;
import dev.ontoharness.spring.OntoHarnessClient;

/**
 * Minimal walkthrough of OntologyValidationAdvisor against a running sidecar.
 * Run with: {@code mvn -q -Dtest=BasicUsageExampleTest test}
 */
public final class BasicUsageExample {

    public static void main(String[] args) {
        run("http://localhost:8010").forEach(System.out::println);
    }

    static List<String> run(String baseUrl) {
        var client = new OntoHarnessClient(baseUrl);
        var policy = OntologyValidationPolicy.builder(client)
                .domain("biomedical")
                .failClosed(true)
                .validateOutput(true)
                .build();
        var advisor = OntologyValidationAdvisor.advisor(policy).build();

        ChatClientResponse valid = advisor.adviseCall(
                request("valid"), chainWithAssistant(validAssistantText()));
        ChatClientResponse blocked = advisor.adviseCall(
                request("fabricated"), chainWithAssistant(fabricatedAssistantText()));

        return List.of(
                "Valid scenario conforms="
                        + !Boolean.FALSE.equals(valid.context().get(OntologyValidationAdvisor.CONTEXT_ONTOLOGY_CONFORMS)),
                "Fabricated scenario blocked="
                        + Boolean.FALSE.equals(blocked.context().get(OntologyValidationAdvisor.CONTEXT_ONTOLOGY_CONFORMS)),
                "Repair hints="
                        + blocked.context().getOrDefault(OntologyValidationAdvisor.CONTEXT_ONTOLOGY_HINTS, List.of()));
    }

    private static ChatClientRequest request(String scenario) {
        return ChatClientRequest.builder()
                .prompt(new Prompt(new UserMessage("scenario:" + scenario)))
                .context(Map.of())
                .build();
    }

    private static CallAdvisorChain chainWithAssistant(String assistantText) {
        return new CallAdvisorChain() {
            @Override
            public ChatClientResponse nextCall(ChatClientRequest request) {
                return ChatClientResponse.builder()
                        .chatResponse(ChatResponse.builder()
                                .generations(List.of(new Generation(new AssistantMessage(assistantText))))
                                .build())
                        .context(request.context())
                        .build();
            }

            @Override
            public List<CallAdvisor> getCallAdvisors() {
                return List.of();
            }
        };
    }

    private static String validAssistantText() {
        return """
                ```turtle
                @prefix bio: <https://ontoharness.dev/biomedical#> .
                bio:gene1 a bio:Gene ;
                    bio:hasSymbol "BRCA1" ;
                    bio:associatedWith bio:disease1 ;
                    bio:hasScore "0.92"^^<http://www.w3.org/2001/XMLSchema#decimal> .
                bio:disease1 a bio:Disease ;
                    bio:hasIdentifier "MONDO:0007254" .
                ```
                """;
    }

    private static String fabricatedAssistantText() {
        return """
                ```turtle
                @prefix bio: <https://ontoharness.dev/biomedical#> .
                bio:gene1 a bio:Gene ;
                    bio:hasTherapeuticTarget bio:disease1 .
                bio:disease1 a bio:Disease .
                ```
                """;
    }

    private BasicUsageExample() {}
}
