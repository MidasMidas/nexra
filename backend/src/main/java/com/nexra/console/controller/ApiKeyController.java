package com.nexra.console.controller;

import com.nexra.console.dto.ApiKeyCreateRequest;
import com.nexra.console.model.ApiKeyRecord;
import com.nexra.console.service.NexraService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/keys")
@CrossOrigin(origins = "*")
public class ApiKeyController {
    private final NexraService nexraService;

    public ApiKeyController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping
    public List<ApiKeyRecord> getApiKeys(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.getApiKeys();
    }

    @PostMapping
    public ApiKeyRecord createApiKey(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @Valid @RequestBody ApiKeyCreateRequest request
    ) {
        nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.createApiKey(request);
    }
}
