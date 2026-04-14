package com.nexra.console.controller;

import com.nexra.console.dto.LoginRequest;
import com.nexra.console.dto.LoginResponse;
import com.nexra.console.dto.MessageResponse;
import com.nexra.console.dto.RegisterRequest;
import com.nexra.console.service.NexraService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/auth")
@CrossOrigin(origins = "*")
public class AuthController {
    private final NexraService nexraService;

    public AuthController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @PostMapping("/login")
    public LoginResponse login(@Valid @RequestBody LoginRequest request) {
        return nexraService.login(request);
    }

    @PostMapping("/register")
    public LoginResponse register(@Valid @RequestBody RegisterRequest request) {
        return nexraService.register(request);
    }

    @PostMapping("/logout")
    public MessageResponse logout(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.logout(authorization);
        return new MessageResponse("Logged out.");
    }
}
