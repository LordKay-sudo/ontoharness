package dev.ontoharness.spring;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class TurtleBlockExtractorTest {

    @Test
    void extractsSingleTurtleFence() {
        String text =
                """
                Here is the graph:
                ```turtle
                @prefix bio: <https://ontoharness.dev/biomedical#> .
                bio:g1 a bio:Gene .
                ```
                """;
        assertEquals(1, TurtleBlockExtractor.extract(text).size());
        assertTrue(TurtleBlockExtractor.extract(text).get(0).contains("bio:Gene"));
    }

    @Test
    void ignoresNonTurtleFences() {
        String text = "```json\n{\"a\":1}\n```";
        assertTrue(TurtleBlockExtractor.extract(text).isEmpty());
    }
}
