package com.nexra.console.dto;

public record LoginResponse(
        String token,
        UserResponse user
) {
}
