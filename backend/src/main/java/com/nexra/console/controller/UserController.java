package com.nexra.console.controller;

import com.nexra.console.dto.UserProfileResponse;
import com.nexra.console.dto.UserResponse;
import com.nexra.console.service.NexraService;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/users")
@CrossOrigin(origins = "*")
public class UserController {
    private final NexraService nexraService;

    public UserController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping
    public List<UserResponse> getUsers(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.requireAdminAuthorization(authorization);
        return nexraService.getUsers();
    }

    @GetMapping("/me")
    public UserProfileResponse getProfile(@RequestHeader(value = "Authorization", required = false) String authorization) {
        String userId = nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.getUserProfile(userId);
    }
}
