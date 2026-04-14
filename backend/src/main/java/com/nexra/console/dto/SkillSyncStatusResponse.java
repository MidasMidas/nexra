package com.nexra.console.dto;

public record SkillSyncStatusResponse(
        boolean enabled,
        boolean inProgress,
        String dataFile,
        int targetCount,
        int currentImportedCount,
        String lastAttemptAt,
        String lastSuccessAt,
        String lastError,
        int lastImportedCount
) {
}
