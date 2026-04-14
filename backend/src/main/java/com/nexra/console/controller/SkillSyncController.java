package com.nexra.console.controller;

import com.nexra.console.dto.SkillSyncStatusResponse;
import com.nexra.console.service.NexraService;
import com.nexra.console.service.SkillSyncService;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin/skills/sync")
@CrossOrigin(origins = "*")
public class SkillSyncController {
    private final NexraService nexraService;
    private final SkillSyncService skillSyncService;

    public SkillSyncController(NexraService nexraService, SkillSyncService skillSyncService) {
        this.nexraService = nexraService;
        this.skillSyncService = skillSyncService;
    }

    @GetMapping("/status")
    public SkillSyncStatusResponse getStatus(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.requireAdminAuthorization(authorization);
        return skillSyncService.status();
    }

    @PostMapping
    public SkillSyncStatusResponse triggerSync(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.requireAdminAuthorization(authorization);
        return skillSyncService.syncNow();
    }
}
