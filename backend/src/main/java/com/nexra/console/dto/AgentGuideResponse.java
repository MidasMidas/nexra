package com.nexra.console.dto;

import java.util.List;

public record AgentGuideResponse(
        String name,
        String goal,
        String invokeEndpoint,
        List<String> workflow,
        List<String> rules,
        ExampleCall exampleCall
) {
    public record ExampleCall(
            String method,
            String endpoint,
            String contentType,
            String payload
    ) {
    }
}
