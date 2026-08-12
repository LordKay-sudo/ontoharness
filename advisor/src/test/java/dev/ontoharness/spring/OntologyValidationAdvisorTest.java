package dev.ontoharness.spring;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.ai.chat.prompt.Prompt;

class OntologyValidationAdvisorTest {

    @Test
    void blocksFabricatedTurtleInAssistantOutput() {
        OntoHarnessClient client = mock(OntoHarnessClient.class);
        when(client.validate(any(), any()))
                .thenReturn(new OntoHarnessClient.ValidationResponse(
                        "biomedical", false, List.of("Remove undeclared predicate bio:hasTherapeuticTarget")));

        var policy = OntologyValidationPolicy.builder(client)
                .domain("biomedical")
                .failClosed(true)
                .validateOutput(true)
                .build();
        var advisor = OntologyValidationAdvisor.advisor(policy).build();

        CallAdvisorChain chain = mock(CallAdvisorChain.class);
        when(chain.nextCall(any())).thenReturn(assistantResponse(fabricatedAssistantText()));

        ChatClientResponse response = advisor.adviseCall(userRequest("propose a gene link"), chain);

        assertThat(response.context()).containsEntry(OntologyValidationAdvisor.CONTEXT_ONTOLOGY_CONFORMS, false);
        assertThat(response.chatResponse().getResult().getOutput().getText())
                .contains("Response blocked");
        verify(client).validate(any(), any());
    }

    @Test
    void passesThroughValidTurtleInAssistantOutput() {
        OntoHarnessClient client = mock(OntoHarnessClient.class);
        when(client.validate(any(), any()))
                .thenReturn(new OntoHarnessClient.ValidationResponse("biomedical", true, List.of()));

        var policy = OntologyValidationPolicy.builder(client)
                .domain("biomedical")
                .failClosed(true)
                .validateOutput(true)
                .build();
        var advisor = OntologyValidationAdvisor.advisor(policy).build();

        CallAdvisorChain chain = mock(CallAdvisorChain.class);
        ChatClientResponse modelResponse = assistantResponse(validAssistantText());
        when(chain.nextCall(any())).thenReturn(modelResponse);

        ChatClientResponse response = advisor.adviseCall(userRequest("propose a gene link"), chain);

        assertThat(response).isSameAs(modelResponse);
        ArgumentCaptor<String> turtleCaptor = ArgumentCaptor.forClass(String.class);
        verify(client).validate(any(), turtleCaptor.capture());
        assertThat(turtleCaptor.getValue()).contains("bio:hasSymbol").doesNotContain("```");
    }

    private static ChatClientRequest userRequest(String text) {
        return ChatClientRequest.builder()
                .prompt(new Prompt(new UserMessage(text)))
                .context(Map.of())
                .build();
    }

    private static ChatClientResponse assistantResponse(String text) {
        return ChatClientResponse.builder()
                .chatResponse(ChatResponse.builder()
                        .generations(List.of(new Generation(new AssistantMessage(text))))
                        .build())
                .context(Map.of())
                .build();
    }

    private static String validAssistantText() {
        return """
                Here is the proposed graph:
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
}
