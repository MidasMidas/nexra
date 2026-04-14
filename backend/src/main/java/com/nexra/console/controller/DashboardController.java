package com.nexra.console.controller;

import com.nexra.console.dto.DashboardResponse;
import com.nexra.console.service.NexraService;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/dashboard")
@CrossOrigin(origins = "*")
public class DashboardController {
    private final NexraService nexraService;

    public DashboardController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping
    public DashboardResponse getDashboard() {
        return nexraService.getDashboard();
    }
}
