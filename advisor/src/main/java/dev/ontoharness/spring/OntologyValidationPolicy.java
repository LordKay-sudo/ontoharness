package dev.ontoharness.spring;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Policy for {@link OntologyValidationAdvisor} — validates Turtle via OntoHarness sidecar.
 */
public final class OntologyValidationPolicy {

    private final OntoHarnessClient client;
    private final String domain;
    private final boolean failClosed;
    private final boolean validateInput;
    private final boolean validateOutput;

    private OntologyValidationPolicy(Builder builder) {
        this.client = Objects.requireNonNull(builder.client, "client");
        this.domain = Objects.requireNonNull(builder.domain, "domain");
        this.failClosed = builder.failClosed;
        this.validateInput = builder.validateInput;
        this.validateOutput = builder.validateOutput;
    }

    public static Builder builder(OntoHarnessClient client) {
        return new Builder(client);
    }

    public String domain() {
        return domain;
    }

    public boolean failClosed() {
        return failClosed;
    }

    public boolean validateInput() {
        return validateInput;
    }

    public boolean validateOutput() {
        return validateOutput;
    }

    public ValidationOutcome validateTurtle(String turtle) {
        if (turtle == null || turtle.isBlank()) {
            return ValidationOutcome.pass();
        }
        OntoHarnessClient.ValidationResponse response = client.validate(domain, turtle);
        if (response.conforms()) {
            return ValidationOutcome.pass();
        }
        return ValidationOutcome.fail(response.repairHints());
    }

    public record ValidationOutcome(boolean conforms, List<String> repairHints) {
        public static ValidationOutcome pass() {
            return new ValidationOutcome(true, List.of());
        }

        public static ValidationOutcome fail(List<String> hints) {
            return new ValidationOutcome(false, hints == null ? List.of() : List.copyOf(hints));
        }
    }

    public static final class Builder {
        private final OntoHarnessClient client;
        private String domain = "biomedical";
        private boolean failClosed = true;
        private boolean validateInput = false;
        private boolean validateOutput = true;

        private Builder(OntoHarnessClient client) {
            this.client = client;
        }

        public Builder domain(String domain) {
            this.domain = domain;
            return this;
        }

        public Builder failClosed(boolean failClosed) {
            this.failClosed = failClosed;
            return this;
        }

        public Builder validateInput(boolean validateInput) {
            this.validateInput = validateInput;
            return this;
        }

        public Builder validateOutput(boolean validateOutput) {
            this.validateOutput = validateOutput;
            return this;
        }

        public OntologyValidationPolicy build() {
            return new OntologyValidationPolicy(this);
        }
    }
}
