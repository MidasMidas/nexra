package com.nexra.console.dto;

import java.util.List;

public record PaginatedResponse<T>(
        List<T> items,
        int page,
        int pageSize,
        long totalItems,
        int totalPages
) {
}
