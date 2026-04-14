package com.nexra.console.controller;

import com.nexra.console.dto.AgentGuideResponse;
import com.nexra.console.dto.WelcomeResponse;
import com.nexra.console.service.NexraService;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class GuideController {
    private final NexraService nexraService;

    public GuideController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping
    public WelcomeResponse getWelcome() {
        return nexraService.getWelcome();
    }

    @GetMapping("/agent-guide")
    public AgentGuideResponse getAgentGuide() {
        return nexraService.getAgentGuide();
    }
}
