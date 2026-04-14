package com.nexra.console.controller;

import com.nexra.console.dto.ReviewRequest;
import com.nexra.console.dto.ReviewResponse;
import com.nexra.console.dto.PaginatedResponse;
import com.nexra.console.dto.SkillCreateRequest;
import com.nexra.console.dto.SkillDetailResponse;
import com.nexra.console.dto.SkillResponse;
import com.nexra.console.service.NexraService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/skills")
@CrossOrigin(origins = "*")
public class SkillController {
    private final NexraService nexraService;

    public SkillController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping
    public PaginatedResponse<SkillResponse> getSkills(
            @RequestParam(required = false) String q,
            @RequestParam(required = false, name = "function") String functionName,
            @RequestParam(required = false) String readiness,
            @RequestParam(defaultValue = "false") boolean hideTemplates,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int pageSize
    ) {
        return nexraService.getSkills(q, functionName, readiness, hideTemplates, page, pageSize, false);
    }

    @GetMapping("/{id}")
    public SkillDetailResponse getSkill(@PathVariable String id) {
        return nexraService.getSkill(id);
    }

    @PostMapping("/{id}/reviews")
    public ReviewResponse addReview(
            @PathVariable String id,
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody ReviewRequest request
    ) {
        String authenticatedUserId = nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.addReview(id, authenticatedUserId, request);
    }

    @PostMapping("/submissions")
    public SkillResponse submitSkill(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody SkillCreateRequest request
    ) {
        String authenticatedUserId = nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.submitSkill(authenticatedUserId, request);
    }
}
