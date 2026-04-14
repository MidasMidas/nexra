package com.nexra.console.dto;

import java.util.List;

public record WelcomeResponse(
        String productName,
        String headline,
        String summary,
        List<String> steps,
        List<String> capabilities,
        String frontendUrl,
        String agentGuideUrl
) {
}
