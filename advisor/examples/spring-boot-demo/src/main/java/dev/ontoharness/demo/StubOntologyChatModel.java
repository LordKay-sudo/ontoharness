package dev.ontoharness.demo;

import java.util.List;

import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.stereotype.Component;

import reactor.core.publisher.Flux;

/**
 * Stub model for offline demos — returns Turtle scenarios without calling OpenAI.
 * Prompt must contain {@code scenario:valid} or {@code scenario:fabricated}.
 */
@Component
public class StubOntologyChatModel implements ChatModel {

    private static final String VALID = """
            Here is the proposed biomedical graph:
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

    private static final String FABRICATED = """
            Proposed association:
            ```turtle
            @prefix bio: <https://ontoharness.dev/biomedical#> .
            bio:gene1 a bio:Gene ;
                bio:hasTherapeuticTarget bio:disease1 .
            bio:disease1 a bio:Disease .
            ```
            """;

    @Override
    public ChatResponse call(Prompt prompt) {
        return new ChatResponse(List.of(new Generation(new AssistantMessage(assistantText(prompt)))));
    }

    @Override
    public Flux<ChatResponse> stream(Prompt prompt) {
        return Flux.just(call(prompt));
    }

    private static String assistantText(Prompt prompt) {
        String text = prompt.getUserMessage().getText().toLowerCase();
        return text.contains("fabricated") ? FABRICATED : VALID;
    }
}
