package dev.ontoharness.spring;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Extracts ```turtle ... ``` blocks from LLM output for OntoHarness validation.
 * v0.2 helper — full Spring AI CallAdvisor wiring lands in 0.4.
 */
public final class TurtleBlockExtractor {

    private static final Pattern TURTLE_FENCE =
            Pattern.compile("```(?:turtle|ttl)\\s*([\\s\\S]*?)```", Pattern.CASE_INSENSITIVE);

    private TurtleBlockExtractor() {}

    public static List<String> extract(String text) {
        if (text == null || text.isBlank()) {
            return List.of();
        }
        return TURTLE_FENCE.matcher(text).results().map(Matcher::group).map(String::trim).filter(s -> !s.isEmpty()).toList();
    }
}
