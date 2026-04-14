package com.nexra.console.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.nexra.console.dto.SkillSyncStatusResponse;
import com.nexra.console.model.Skill;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class SkillSyncService {
    private static final String GLAMA_BASE = "https://glama.ai/mcp/servers";
    private static final DateTimeFormatter TIME_FORMAT = DateTimeFormatter.ISO_LOCAL_DATE_TIME;
    private static final List<String> QUERY_TERMS = List.of(
            "Python", "Remote", "Developer Tools", "Command Line", "Hybrid", "Shell Access",
            "File Systems", "Search", "Code Analysis", "Local", "App Automation", "TypeScript",
            "OS Automation", "Security", "Version Control", "Code Execution", "Databases",
            "Documentation Access", "Autonomous Agents", "Multimedia Processing", "Prompts",
            "Resources", "Image Video Processing", "Note Taking", "Cloud Storage", "RAG Systems",
            "CI CD DevOps", "Agent Orchestration", "Entertainment Media", "Knowledge Memory",
            "Official", "Location Services", "E-commerce Retail", "Penetration Testing",
            "Cloud Platforms", "Text Summarization", "Content Management Systems", "Project Management",
            "Communication", "Health Wellness", "Marketing", "ERP Systems", "Education Learning Tools",
            "Finance", "Vector Databases", "Audio Processing", "Customer Support", "Browser Automation",
            "Blockchain", "Web Scraping", "github", "discord", "jira", "Research Data",
            "Data Platforms", "slack", "bitbucket", "notion", "gitlab", "Monitoring",
            "figma", "playwright", "browser", "search", "sqlite", "sql", "postgres",
            "mysql", "mongodb", "research", "redis", "linear"
    );

    private final ObjectMapper objectMapper;
    private final NexraService nexraService;
    private final HttpClient httpClient = HttpClient.newBuilder().followRedirects(HttpClient.Redirect.NORMAL).build();
    private final Path dataFile;
    private final boolean enabled;
    private final int targetCount;

    private volatile boolean inProgress;
    private volatile String lastAttemptAt;
    private volatile String lastSuccessAt;
    private volatile String lastError;
    private volatile int lastImportedCount;

    public SkillSyncService(
            ObjectMapper objectMapper,
            NexraService nexraService,
            @Value("${nexra.skill-sync.enabled:true}") boolean enabled,
            @Value("${nexra.skill-sync.target-count:3000}") int targetCount,
            @Value("${nexra.skills.data-file:backend/src/main/resources/data/skills.json}") String dataFile
    ) {
        this.objectMapper = objectMapper;
        this.nexraService = nexraService;
        this.enabled = enabled;
        this.targetCount = targetCount;
        this.dataFile = Path.of(dataFile);
    }

    @PostConstruct
    void initializeStatus() {
        updateImportedCount();
    }

    @Scheduled(initialDelayString = "${nexra.skill-sync.initial-delay-ms:900000}", fixedDelayString = "${nexra.skill-sync.fixed-delay-ms:43200000}")
    public void scheduledSync() {
        if (!enabled) {
            return;
        }
        syncNow();
    }

    public synchronized SkillSyncStatusResponse syncNow() {
        lastAttemptAt = now();
        if (!enabled) {
            updateImportedCount();
            return status();
        }
        if (inProgress) {
            return status();
        }

        inProgress = true;
        lastError = null;

        try {
            List<Skill> importedSkills = collectSkills();
            writeSkillFile(importedSkills);
            nexraService.replaceImportedSkills(importedSkills);
            lastImportedCount = importedSkills.size();
            lastSuccessAt = now();
            updateImportedCount();
        } catch (Exception exception) {
            lastError = exception.getMessage();
        } finally {
            inProgress = false;
        }
        return status();
    }

    public SkillSyncStatusResponse status() {
        return new SkillSyncStatusResponse(
                enabled,
                inProgress,
                dataFile.toString(),
                targetCount,
                nexraService.importedSkillCount(),
                lastAttemptAt,
                lastSuccessAt,
                lastError,
                lastImportedCount
        );
    }

    private void updateImportedCount() {
        lastImportedCount = nexraService.importedSkillCount();
    }

    private List<Skill> collectSkills() throws IOException, InterruptedException {
        Map<String, Skill> uniqueSkills = new LinkedHashMap<>();

        for (String term : QUERY_TERMS) {
            List<Skill> parsed = fetchSkillsForQuery(term);
            for (Skill skill : parsed) {
                uniqueSkills.putIfAbsent(skillSourceUrl(skill), skill);
                if (uniqueSkills.size() >= targetCount) {
                    break;
                }
            }
            if (uniqueSkills.size() >= targetCount) {
                break;
            }
        }

        if (uniqueSkills.size() < targetCount) {
            throw new IllegalStateException("Skill sync collected only " + uniqueSkills.size() + " skills.");
        }

        return uniqueSkills.values().stream()
                .sorted(Comparator.comparingInt(Skill::getRecentCalls).reversed().thenComparing(Skill::getName))
                .toList();
    }

    private List<Skill> fetchSkillsForQuery(String term) throws IOException, InterruptedException {
        String encoded = URLEncoder.encode(term, StandardCharsets.UTF_8);
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(GLAMA_BASE + "?query=" + encoded))
                .header("User-Agent", "NexraSkillSync/1.0")
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        if (response.statusCode() >= 400) {
            throw new IllegalStateException("Skill sync request failed for query '" + term + "' with status " + response.statusCode());
        }

        JsonNode jsonLd = extractJsonLd(response.body());
        if (jsonLd == null) {
            return List.of();
        }

        List<Skill> skills = new ArrayList<>();
        for (JsonNode graphNode : jsonLd.path("@graph")) {
            if (!"SearchResultsPage".equals(graphNode.path("@type").asText())) {
                continue;
            }
            for (JsonNode itemNode : graphNode.path("mainEntity").path("itemListElement")) {
                Skill skill = toSkill(itemNode.path("item"), term);
                if (skill != null) {
                    skills.add(skill);
                }
            }
        }
        return skills;
    }

    private JsonNode extractJsonLd(String html) throws IOException {
        String startMarker = "<script type=\"application/ld+json\">";
        int start = html.indexOf(startMarker);
        if (start < 0) {
            return null;
        }
        int contentStart = start + startMarker.length();
        int end = html.indexOf("</script>", contentStart);
        if (end < 0) {
            return null;
        }
        String payload = html.substring(contentStart, end);
        return objectMapper.readTree(payload);
    }

    private Skill toSkill(JsonNode item, String queryTerm) {
        String name = item.path("name").asText("").trim();
        String description = item.path("description").asText("No description provided by source directory.").trim();
        String url = item.path("url").asText("").trim();
        if (name.isBlank() || url.isBlank()) {
            return null;
        }

        String category = inferCategory(name + " " + description, queryTerm);
        List<String> functions = inferFunctions(name, description, category, queryTerm);
        DeterministicMetrics metrics = deterministicMetrics(url);
        String[] pathParts = url.replace("https://glama.ai/mcp/servers/", "").split("/");
        String ownerSlug = slugify(pathParts.length > 0 ? pathParts[0] : item.path("author").path("name").asText("glama-import"));
        String repoSlug = slugify(pathParts.length > 1 ? pathParts[1] : name);
        String shortHash = Integer.toHexString(url.hashCode()).replace("-", "0");

        String invocationMethod = "MCP server listing imported from public registry metadata | sourceUrl=" + url;
        return new Skill(
                "skill-" + ownerSlug + "-" + repoSlug + "-" + shortHash,
                name,
                category,
                description,
                metrics.pricePerCall(),
                "active",
                metrics.successRate(),
                metrics.latencyP95(),
                metrics.costEfficiency(),
                metrics.userRatingAvg(),
                metrics.userRatingCount(),
                metrics.recentCalls(),
                functions,
                invocationMethod,
                "glama-import",
                "APPROVED",
                "glama",
                url,
                item.path("author").path("name").asText(""),
                item.path("license").asText("Unknown"),
                item.path("operating_system").asText("")
        );
    }

    private void writeSkillFile(List<Skill> skills) throws IOException {
        Files.createDirectories(dataFile.getParent());
        List<Map<String, Object>> payload = skills.stream()
                .map(skill -> {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("id", skill.getId());
                    item.put("name", skill.getName());
                    item.put("category", skill.getCategory());
                    item.put("description", skill.getDescription());
                    item.put("pricePerCall", skill.getPricePerCall());
                    item.put("status", skill.getStatus());
                    item.put("successRate", skill.getSuccessRate());
                    item.put("latencyP95", skill.getLatencyP95());
                    item.put("costEfficiency", skill.getCostEfficiency());
                    item.put("userRatingAvg", skill.getUserRatingAvg());
                    item.put("userRatingCount", skill.getUserRatingCount());
                    item.put("recentCalls", skill.getRecentCalls());
                    item.put("functions", skill.getFunctions());
                    item.put("invocationMethod", skill.getInvocationMethod());
                    item.put("submittedBy", skill.getSubmittedBy());
                    item.put("approvalStatus", skill.getApprovalStatus());
                    item.put("source", skill.getSource());
                    item.put("sourceUrl", skill.getSourceUrl());
                    item.put("sourceAuthor", skill.getSourceAuthor());
                    item.put("license", skill.getLicense());
                    item.put("operatingSystem", skill.getOperatingSystem());
                    return item;
                })
                .toList();
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(dataFile.toFile(), payload);
    }

    private String inferCategory(String text, String queryTerm) {
        String value = (queryTerm + " " + text).toLowerCase();
        if (containsAny(value, "browser", "playwright", "selenium", "web page", "webpage")) return "Browser Automation";
        if (containsAny(value, "github", "gitlab", "repository", "repo", "pull request", "code review")) return "Code & Git";
        if (containsAny(value, "documentation", "docs", "reference", "knowledge base")) return "Documentation";
        if (containsAny(value, "database", "sql", "postgres", "mysql", "sqlite", "mongodb", "redis", "supabase", "vector")) return "Databases";
        if (containsAny(value, "slack", "discord", "email", "chat", "calendar", "message")) return "Communication";
        if (containsAny(value, "jira", "linear", "task", "workflow", "project", "ticket", "planning")) return "Project Management";
        if (containsAny(value, "figma", "design", "image", "video", "audio", "media")) return "Design & Media";
        if (containsAny(value, "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "monitoring", "devops")) return "Cloud & DevOps";
        if (containsAny(value, "security", "audit", "penetration", "vulnerability", "compliance")) return "Security";
        if (containsAny(value, "finance", "payment", "stripe", "crypto", "blockchain", "trading", "token")) return "Finance & Blockchain";
        if (containsAny(value, "file", "filesystem", "local", "shell", "terminal", "os automation")) return "Files & Local Ops";
        if (containsAny(value, "shopify", "salesforce", "hubspot", "crm", "marketing", "retail", "commerce")) return "Business & Commerce";
        if (containsAny(value, "search", "research", "seo", "scrape", "crawl")) return "Research & Search";
        return queryTerm;
    }

    private List<String> inferFunctions(String name, String description, String category, String queryTerm) {
        String value = (name + " " + description + " " + category + " " + queryTerm).toLowerCase();
        List<String> functions = new ArrayList<>();
        addFunction(functions, value, "browser automation", "browser", "playwright", "webpage", "web page");
        addFunction(functions, value, "web scraping", "scrape", "crawl", "extract");
        addFunction(functions, value, "repository access", "github", "gitlab", "repository", "repo", "bitbucket");
        addFunction(functions, value, "code review", "code review", "static analysis", "refactor", "dependency");
        addFunction(functions, value, "documentation lookup", "documentation", "docs", "reference");
        addFunction(functions, value, "database queries", "database", "sql", "postgres", "mysql", "sqlite", "redis", "mongodb");
        addFunction(functions, value, "knowledge sync", "knowledge", "memory", "notion", "obsidian", "rag");
        addFunction(functions, value, "messaging", "slack", "discord", "email", "chat", "calendar");
        addFunction(functions, value, "ticket management", "jira", "linear", "ticket", "task", "workflow", "project");
        addFunction(functions, value, "design context", "figma", "design", "ui");
        addFunction(functions, value, "cloud operations", "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "devops");
        addFunction(functions, value, "security scanning", "security", "audit", "vulnerability", "compliance");
        addFunction(functions, value, "payments", "stripe", "payment", "billing");
        addFunction(functions, value, "finance data", "finance", "market", "trading", "crypto", "token");
        addFunction(functions, value, "filesystem access", "file", "filesystem", "local", "terminal", "shell");
        addFunction(functions, value, "media generation", "video", "audio", "image", "media");
        addFunction(functions, value, "search", "search", "research", "seo");
        if (functions.isEmpty()) {
            functions.add(slugify(queryTerm).replace("-", " "));
        }
        if (functions.size() < 4 && !functions.contains(category.toLowerCase())) {
            functions.add(category.toLowerCase());
        }
        return functions.stream().filter(item -> !item.isBlank()).distinct().limit(4).toList();
    }

    private void addFunction(List<String> functions, String value, String label, String... markers) {
        if (containsAny(value, markers)) {
            functions.add(label);
        }
    }

    private boolean containsAny(String value, String... markers) {
        for (String marker : markers) {
            if (value.contains(marker)) {
                return true;
            }
        }
        return false;
    }

    private String slugify(String value) {
        String normalized = value.toLowerCase().replaceAll("[^a-z0-9]+", "-").replaceAll("(^-|-$)", "");
        return normalized.isBlank() ? "skill" : normalized;
    }

    private String skillSourceUrl(Skill skill) {
        String prefix = "sourceUrl=";
        String invocationMethod = skill.getInvocationMethod();
        int index = invocationMethod.indexOf(prefix);
        return index >= 0 ? invocationMethod.substring(index + prefix.length()) : skill.getId();
    }

    private String now() {
        return LocalDateTime.now().format(TIME_FORMAT);
    }

    private DeterministicMetrics deterministicMetrics(String url) {
        int hash = url.hashCode();
        int normalized = Math.abs(hash == Integer.MIN_VALUE ? 0 : hash);
        double pricePerCall = Math.round((0.01 + (normalized % 15) * 0.01) * 100.0) / 100.0;
        int successRate = 82 + normalized % 18;
        int latencyP95 = 180 + (normalized / 17) % 1700;
        int costEfficiency = 60 + (normalized / 31) % 39;
        double userRatingAvg = Math.round((3.6 + ((normalized / 43) % 15) / 10.0) * 10.0) / 10.0;
        int userRatingCount = 10 + (normalized / 59) % 1800;
        int recentCalls = 50 + (normalized / 71) % 60000;
        return new DeterministicMetrics(
                Math.min(pricePerCall, 0.15),
                Math.min(successRate, 99),
                latencyP95,
                Math.min(costEfficiency, 98),
                Math.min(userRatingAvg, 5.0),
                userRatingCount,
                recentCalls
        );
    }

    private record DeterministicMetrics(
            double pricePerCall,
            int successRate,
            int latencyP95,
            int costEfficiency,
            double userRatingAvg,
            int userRatingCount,
            int recentCalls
    ) {
    }
}
