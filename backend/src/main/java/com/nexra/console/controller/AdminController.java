package com.nexra.console.controller;

import com.nexra.console.dto.SkillResponse;
import com.nexra.console.dto.SkillUpdateRequest;
import com.nexra.console.service.NexraService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/admin")
@CrossOrigin(origins = "*")
public class AdminController {
    private final NexraService nexraService;

    public AdminController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping("/skills/pending")
    public List<SkillResponse> getPendingSkills(@RequestHeader(value = "Authorization", required = false) String authorization) {
        String authenticatedUserId = nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.getPendingSkills(authenticatedUserId);
    }

    @PostMapping("/skills/{id}/approve")
    public SkillResponse approveSkill(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @PathVariable String id
    ) {
        String authenticatedUserId = nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.approveSkill(authenticatedUserId, id);
    }

    @PutMapping("/skills/{id}")
    public SkillResponse updateSkill(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @PathVariable String id,
            @Valid @RequestBody SkillUpdateRequest request
    ) {
        String authenticatedUserId = nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.adminUpdateSkill(authenticatedUserId, id, request);
    }

    @DeleteMapping("/skills/{id}")
    public void deleteSkill(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @PathVariable String id
    ) {
        String authenticatedUserId = nexraService.requireAuthenticatedUserId(authorization);
        nexraService.adminDeleteSkill(authenticatedUserId, id);
    }
}
