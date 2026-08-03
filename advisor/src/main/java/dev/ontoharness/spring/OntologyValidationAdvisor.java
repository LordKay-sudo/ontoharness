package dev.ontoharness.spring;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;
import org.springframework.ai.chat.client.advisor.api.StreamAdvisor;
import org.springframework.ai.chat.client.advisor.api.StreamAdvisorChain;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.model.Generation;
import org.springframework.core.Ordered;

import reactor.core.publisher.Flux;

/**
 * Post-call Spring AI advisor: validates {@code ```turtle ```} blocks in model output via OntoHarness.
 * Does not call an LLM — only the deterministic sidecar.
 */
public final class OntologyValidationAdvisor implements CallAdvisor, StreamAdvisor {

    public static final String CONTEXT_ONTOLOGY_CONFORMS = "ontoharness.conforms";
    public static final String CONTEXT_ONTOLOGY_HINTS = "ontoharness.repairHints";

    private static final int DEFAULT_ORDER = Ordered.HIGHEST_PRECEDENCE + 60;

    private static final String DEFAULT_FAILURE_RESPONSE =
            "Response blocked: RDF Turtle failed OntoHarness semantic validation (vocab gate + SHACL).";

    private final OntologyValidationPolicy policy;
    private final int order;
    private final String failureResponse;

    private OntologyValidationAdvisor(OntologyValidationPolicy policy, int order, String failureResponse) {
        this.policy = Objects.requireNonNull(policy, "policy");
        this.order = order;
        this.failureResponse = Objects.requireNonNull(failureResponse, "failureResponse");
    }

    public static OntologyValidationPolicy.Builder builder(OntoHarnessClient client) {
        return OntologyValidationPolicy.builder(client);
    }

    public static AdvisorBuilder advisor(OntologyValidationPolicy policy) {
        return new AdvisorBuilder(policy);
    }

    @Override
    public String getName() {
        return getClass().getSimpleName();
    }

    @Override
    public int getOrder() {
        return order;
    }

    @Override
    public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        if (policy.validateInput()) {
            ChatClientResponse inputBlock = validateInputMessages(request);
            if (inputBlock != null) {
                return inputBlock;
            }
        }

        ChatClientResponse response = chain.nextCall(request);

        if (!policy.validateOutput()) {
            return response;
        }

        return validateAssistantResponse(request, response);
    }

    @Override
    public Flux<ChatClientResponse> adviseStream(ChatClientRequest request, StreamAdvisorChain chain) {
        if (policy.validateInput()) {
            ChatClientResponse inputBlock = validateInputMessages(request);
            if (inputBlock != null) {
                return Flux.just(inputBlock);
            }
        }

        return chain.nextStream(request).map(response -> {
            if (!policy.validateOutput()) {
                return response;
            }
            return validateAssistantResponse(request, response);
        });
    }

    private ChatClientResponse validateInputMessages(ChatClientRequest request) {
        for (Message message : request.prompt().getInstructions()) {
            if (message instanceof UserMessage userMessage) {
                ChatClientResponse blocked = validateText(request, userMessage.getText());
                if (blocked != null) {
                    return blocked;
                }
            }
        }
        return null;
    }

    private ChatClientResponse validateAssistantResponse(
            ChatClientRequest request, ChatClientResponse response) {
        ChatResponse chatResponse = response.chatResponse();
        if (chatResponse == null) {
            return response;
        }
        for (Generation generation : chatResponse.getResults()) {
            AssistantMessage output = generation.getOutput();
            if (output == null) {
                continue;
            }
            ChatClientResponse blocked = validateText(request, output.getText());
            if (blocked != null) {
                return blocked;
            }
        }
        return response;
    }

    private ChatClientResponse validateText(ChatClientRequest request, String text) {
        List<String> blocks = TurtleBlockExtractor.extract(text);
        if (blocks.isEmpty()) {
            return null;
        }

        List<String> allHints = new ArrayList<>();
        for (String block : blocks) {
            OntologyValidationPolicy.ValidationOutcome outcome = policy.validateTurtle(block);
            if (!outcome.conforms()) {
                allHints.addAll(outcome.repairHints());
            }
        }

        if (allHints.isEmpty()) {
            return null;
        }

        if (policy.failClosed()) {
            return failureResponse(request, allHints);
        }
        return null;
    }

    private ChatClientResponse failureResponse(ChatClientRequest request, List<String> hints) {
        String message = failureResponse;
        if (!hints.isEmpty()) {
            message =
                    failureResponse
                            + "\n\nRepair hints:\n- "
                            + hints.stream().distinct().collect(Collectors.joining("\n- "));
        }
        return ChatClientResponse.builder()
                .chatResponse(
                        ChatResponse.builder()
                                .generations(List.of(new Generation(new AssistantMessage(message))))
                                .build())
                .context(
                        Map.of(
                                CONTEXT_ONTOLOGY_CONFORMS,
                                false,
                                CONTEXT_ONTOLOGY_HINTS,
                                hints))
                .build();
    }

    public static final class AdvisorBuilder {
        private final OntologyValidationPolicy policy;
        private int order = DEFAULT_ORDER;
        private String failureResponse = DEFAULT_FAILURE_RESPONSE;

        private AdvisorBuilder(OntologyValidationPolicy policy) {
            this.policy = policy;
        }

        public AdvisorBuilder order(int order) {
            this.order = order;
            return this;
        }

        public AdvisorBuilder failureResponse(String failureResponse) {
            this.failureResponse = failureResponse;
            return this;
        }

        public OntologyValidationAdvisor build() {
            return new OntologyValidationAdvisor(policy, order, failureResponse);
        }
    }
}
