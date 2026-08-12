package dev.ontoharness.demo;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.model.ChatModel;

import dev.ontoharness.spring.OntologyValidationAdvisor;
import dev.ontoharness.spring.OntologyValidationPolicy;
import dev.ontoharness.spring.OntoHarnessClient;

@Configuration
public class DemoConfig {

    @Bean
    OntoHarnessClient ontoHarnessClient(@Value("${ontoharness.base-url}") String baseUrl) {
        return new OntoHarnessClient(baseUrl);
    }

    @Bean
    OntologyValidationAdvisor ontologyValidationAdvisor(OntoHarnessClient client) {
        var policy = OntologyValidationPolicy.builder(client)
                .domain("biomedical")
                .failClosed(true)
                .validateOutput(true)
                .build();
        return OntologyValidationAdvisor.advisor(policy).build();
    }

    @Bean
    ChatClient chatClient(ChatModel chatModel, OntologyValidationAdvisor advisor) {
        return ChatClient.builder(chatModel).defaultAdvisors(advisor).build();
    }
}
