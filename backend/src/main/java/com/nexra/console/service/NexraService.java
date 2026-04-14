package com.nexra.console.service;

import com.nexra.console.dto.ApiKeyCreateRequest;
import com.nexra.console.dto.AgentGuideResponse;
import com.nexra.console.dto.DashboardResponse;
import com.nexra.console.dto.LoginRequest;
import com.nexra.console.dto.LoginResponse;
import com.nexra.console.dto.PaginatedResponse;
import com.nexra.console.dto.RegisterRequest;
import com.nexra.console.dto.ReviewRequest;
import com.nexra.console.dto.ReviewResponse;
import com.nexra.console.dto.SkillCreateRequest;
import com.nexra.console.dto.SkillDetailResponse;
import com.nexra.console.dto.SkillResponse;
import com.nexra.console.dto.SkillUpdateRequest;
import com.nexra.console.dto.UserProfileResponse;
import com.nexra.console.dto.UserReviewResponse;
import com.nexra.console.dto.UserResponse;
import com.nexra.console.dto.WelcomeResponse;
import com.nexra.console.model.ApiKeyRecord;
import com.nexra.console.model.BillingSummary;
import com.nexra.console.model.BillingTransaction;
import com.nexra.console.model.Review;
import com.nexra.console.model.Skill;
import com.nexra.console.model.UserAccount;
import com.nexra.console.repository.ReviewRepository;
import com.nexra.console.repository.SkillRepository;
import com.nexra.console.repository.UserAccountRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.stream.Collectors;

@Service
public class NexraService {
    private final ObjectMapper objectMapper;
    private final Path dataFile;
    private final SkillRepository skillRepository;
    private final ReviewRepository reviewRepository;
    private final UserAccountRepository userAccountRepository;
    private final List<BillingTransaction> transactions = new CopyOnWriteArrayList<>();
    private final List<ApiKeyRecord> apiKeys = new CopyOnWriteArrayList<>();
    private final Map<String, String> sessions = new HashMap<>();

    public NexraService(
            ObjectMapper objectMapper,
            SkillRepository skillRepository,
            ReviewRepository reviewRepository,
            UserAccountRepository userAccountRepository,
            @Value("${nexra.skills.data-file:backend/src/main/resources/data/skills.json}") String dataFile
    ) {
        this.objectMapper = objectMapper;
        this.skillRepository = skillRepository;
        this.reviewRepository = reviewRepository;
        this.userAccountRepository = userAccountRepository;
        this.dataFile = Path.of(dataFile);
    }

    @PostConstruct
    @Transactional
    void seed() {
        if (userAccountRepository.count() == 0) {
            userAccountRepository.saveAll(List.of(
                    new UserAccount("admin_1", "admin@nexra.local", "admin123", "Nexra Admin", "ADMIN"),
                    new UserAccount("user_1", "alice@nexra.local", "alice123", "Alice Builder", "USER"),
                    new UserAccount("user_2", "bob@nexra.local", "bob123", "Bob Operator", "USER")
            ));
        }

        if (skillRepository.count() == 0) {
            loadSkillDatabase();
            skillRepository.save(new Skill("skill-report", "Report Composer", "Productivity",
                    "Drafts structured summaries, release notes, and stakeholder-ready reports from operational events.",
                    0.05, "draft", 90, 480, 79, 0.0, 0, 0,
                    List.of("report generation", "summarization", "release notes"),
                    "REST API with JSON instructions",
                    "user_1",
                    "PENDING",
                    "manual",
                    "https://example.com/report-composer",
                    "Alice Builder",
                    "Proprietary",
                    "Cloud / API"));
        }

        if (transactions.isEmpty()) {
            transactions.add(new BillingTransaction("txn_1001", "Invocation charges", -124.32, "2026-04-09 18:10"));
            transactions.add(new BillingTransaction("txn_1002", "Top-up", 500.00, "2026-04-08 09:30"));
            transactions.add(new BillingTransaction("txn_1003", "Invocation charges", -87.76, "2026-04-07 20:12"));
        }

        if (apiKeys.isEmpty()) {
            apiKeys.add(new ApiKeyRecord("nk_live_01", "Production Search Client", "skills:read", "3 min ago", "active"));
            apiKeys.add(new ApiKeyRecord("nk_test_02", "Staging Agent", "skills:read", "2 hrs ago", "active"));
            apiKeys.add(new ApiKeyRecord("nk_old_03", "Legacy QA", "skills:read", "12 days ago", "revoked"));
        }
    }

    @Transactional
    private void loadSkillDatabase() {
        replaceImportedSkills(readSkillsFromConfiguredSource());
    }

    @Transactional
    public synchronized void replaceImportedSkills(List<Skill> importedSkills) {
        List<String> importedIds = skillRepository.findAll().stream()
                .filter(skill -> "glama-import".equalsIgnoreCase(skill.getSubmittedBy()))
                .map(Skill::getId)
                .toList();
        if (!importedIds.isEmpty()) {
            importedIds.forEach(reviewRepository::deleteBySkillId);
            skillRepository.deleteAllById(importedIds);
        }
        skillRepository.saveAll(importedSkills);
    }

    public synchronized int importedSkillCount() {
        return Math.toIntExact(skillRepository.countBySubmittedByIgnoreCase("glama-import"));
    }

    private List<Skill> readSkillsFromConfiguredSource() {
        try {
            if (Files.exists(dataFile)) {
                try (InputStream inputStream = Files.newInputStream(dataFile)) {
                    return readSkills(inputStream);
                }
            }
            try (InputStream inputStream = getClass().getClassLoader().getResourceAsStream("data/skills.json")) {
                if (inputStream == null) {
                    throw new IllegalArgumentException("skills.json not found in configured file or resources.");
                }
                return readSkills(inputStream);
            }
        } catch (IOException exception) {
            throw new IllegalStateException("Failed to load skill database file.", exception);
        }
    }

    private List<Skill> readSkills(InputStream inputStream) throws IOException {
        JsonNode root = objectMapper.readTree(inputStream);
        List<Skill> loadedSkills = new ArrayList<>();
        for (JsonNode node : root) {
            List<String> functions = new ArrayList<>();
            node.path("functions").forEach(item -> functions.add(item.asText()));
            loadedSkills.add(new Skill(
                    node.path("id").asText(),
                    node.path("name").asText(),
                    node.path("category").asText(),
                    node.path("description").asText(),
                    node.path("pricePerCall").asDouble(),
                    node.path("status").asText(),
                    node.path("successRate").asInt(),
                    node.path("latencyP95").asInt(),
                    node.path("costEfficiency").asInt(),
                    node.path("userRatingAvg").asDouble(),
                    node.path("userRatingCount").asInt(),
                    node.path("recentCalls").asInt(),
                    functions,
                    node.path("invocationMethod").asText(),
                    node.path("submittedBy").asText(),
                    node.path("approvalStatus").asText(),
                    node.path("source").asText("public-registry"),
                    node.path("sourceUrl").asText(""),
                    node.path("sourceAuthor").asText(""),
                    node.path("license").asText("Unknown"),
                    node.path("operatingSystem").asText("")
            ));
        }
        return loadedSkills;
    }

    public DashboardResponse getDashboard() {
        List<Skill> skills = skillRepository.findAll();
        int approvedSkills = (int) skills.stream()
                .filter(skill -> !"revoked".equalsIgnoreCase(skill.getStatus()))
                .filter(skill -> "APPROVED".equalsIgnoreCase(skill.getApprovalStatus()))
                .count();
        int pendingSkills = (int) skills.stream()
                .filter(skill -> "PENDING".equalsIgnoreCase(skill.getApprovalStatus()))
                .count();
        int averageTrust = (int) Math.round(skills.stream().mapToInt(this::overallTrust).average().orElse(0));
        int averageRecommendation = (int) Math.round(skills.stream()
                .mapToInt(skill -> recommendationScore(skill, "", ""))
                .average()
                .orElse(0));
        int searchableFunctions = (int) skills.stream()
                .flatMap(skill -> skill.getFunctions().stream())
                .distinct()
                .count();
        int popularSkills = (int) skills.stream()
                .filter(skill -> skill.getRecentCalls() >= 10_000)
                .count();
        int averageSuccessRate = (int) Math.round(skills.stream().mapToInt(Skill::getSuccessRate).average().orElse(0));
        int averageLatencyP95 = (int) Math.round(skills.stream().mapToInt(Skill::getLatencyP95).average().orElse(0));
        int averageCostEfficiency = (int) Math.round(skills.stream().mapToInt(Skill::getCostEfficiency).average().orElse(0));
        List<SkillResponse> topSkills = skills.stream()
                .filter(skill -> "APPROVED".equalsIgnoreCase(skill.getApprovalStatus()))
                .sorted(Comparator.comparingInt((Skill skill) -> recommendationScore(skill, "", "")).reversed())
                .limit(3)
                .map(skill -> toSkillResponse(skill, "", ""))
                .toList();

        return new DashboardResponse(skills.size(), approvedSkills, pendingSkills, averageTrust, averageRecommendation,
                searchableFunctions, popularSkills,
                averageSuccessRate, averageLatencyP95, averageCostEfficiency, topSkills);
    }

    public WelcomeResponse getWelcome() {
        return new WelcomeResponse(
                "Nexra",
                "Find the right skill before your agent calls it",
                "Nexra helps your agent search, compare, and evaluate external skills with trust signals, recommendation scores, and clear calling guidance.",
                List.of(
                        "Search the marketplace by keyword or capability.",
                        "Compare recommendation score, trust score, price, and calling method.",
                        "Open a skill detail page to read provider docs and calling notes.",
                        "Let your own agent call the external skill directly and come back to Nexra for feedback."
                ),
                List.of(
                        "Search and recommendation for agent-ready skills",
                        "Dual scoring with user rating and system rating",
                        "Moderation, governance, and calling guidance in one place"
                ),
                "http://127.0.0.1:4173",
                "http://localhost:8080/api/agent-guide"
        );
    }

    public AgentGuideResponse getAgentGuide() {
        return new AgentGuideResponse(
                "Nexra Agent Guide",
                "Help any AI agent discover, choose, and call external skills correctly.",
                "/api/skills and /api/skills/{id}",
                List.of(
                        "Fetch available skills from GET /api/skills.",
                        "Compare recommendationScore, overallTrust, userRatingAvg, systemScore, and pricePerCall.",
                        "Select the best skill for the task and read its provider docs.",
                        "Use GET /api/skills/{id} for deeper trust, calling notes, and review context.",
                        "Call the chosen skill directly from your own agent runtime.",
                        "After a human sees the result, submit feedback to POST /api/skills/{id}/reviews."
                ),
                List.of(
                        "Prefer higher recommendationScore when the capability match is strong.",
                        "Use overallTrust as a blended quality signal.",
                        "Use userRatingAvg to estimate human satisfaction.",
                        "Use systemScore to estimate operational reliability.",
                        "Treat provider documentation as the source of truth for external invocation details."
                ),
                new AgentGuideResponse.ExampleCall(
                        "GET",
                        "/api/skills?q=image&function=ocr&page=0&pageSize=5",
                        "application/json",
                        "{\"note\":\"Choose a skill from the search results, then call the provider directly.\"}"
                )
        );
    }

    public PaginatedResponse<SkillResponse> getSkills(
            String query,
            String functionName,
            String readiness,
            boolean hideTemplates,
            int page,
            int pageSize,
            boolean includePending
    ) {
        int safePage = Math.max(page, 0);
        int safePageSize = Math.max(Math.min(pageSize, 50), 1);

        List<SkillResponse> filtered = skillRepository.findAll().stream()
                .filter(skill -> includePending || "APPROVED".equalsIgnoreCase(skill.getApprovalStatus()))
                .filter(skill -> matchesQuery(skill, query))
                .filter(skill -> matchesFunction(skill, functionName))
                .filter(skill -> matchesReadiness(skill, readiness, hideTemplates))
                .sorted(Comparator.comparingInt((Skill skill) -> recommendationScore(skill, query, functionName)).reversed()
                        .thenComparing(Comparator.comparingInt(this::overallTrust).reversed()))
                .map(skill -> toSkillResponse(skill, query, functionName))
                .toList();

        int fromIndex = Math.min(safePage * safePageSize, filtered.size());
        int toIndex = Math.min(fromIndex + safePageSize, filtered.size());
        int totalPages = filtered.isEmpty() ? 0 : (int) Math.ceil((double) filtered.size() / safePageSize);

        return new PaginatedResponse<>(
                filtered.subList(fromIndex, toIndex),
                safePage,
                safePageSize,
                filtered.size(),
                totalPages
        );
    }

    public SkillDetailResponse getSkill(String id) {
        Skill skill = findSkill(id);
        List<ReviewResponse> skillReviews = reviewRepository.findBySkillId(id).stream()
                .sorted(Comparator.comparing(Review::getTimestamp).reversed())
                .map(this::toReviewResponse)
                .toList();
        return new SkillDetailResponse(toSkillResponse(skill, "", ""), skillReviews);
    }

    @Transactional
    public ReviewResponse addReview(String skillId, String userId, ReviewRequest request) {
        Skill skill = findSkill(skillId);
        UserAccount user = requireAuthenticatedUser(userId);
        String comment = request.getComment() == null || request.getComment().isBlank()
                ? "No written feedback left."
                : request.getComment().trim();
        Review review = new Review(
                "rev_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8),
                skillId,
                user.id(),
                user.name(),
                request.getRating(),
                comment,
                LocalDate.now().toString()
        );
        reviewRepository.save(review);
        skill.applyUserRating(request.getRating());
        skillRepository.save(skill);
        return toReviewResponse(review);
    }

    @Transactional
    public SkillResponse submitSkill(String userId, SkillCreateRequest request) {
        UserAccount user = requireAuthenticatedUser(userId);
        Skill skill = new Skill(
                "skill-" + UUID.randomUUID().toString().replace("-", "").substring(0, 8),
                request.getName().trim(),
                request.getCategory().trim(),
                request.getDescription().trim(),
                request.getPricePerCall(),
                "draft",
                request.getSuccessRate(),
                request.getLatencyP95(),
                request.getCostEfficiency(),
                0.0,
                0,
                request.getRecentCalls(),
                sanitizeList(request.getFunctions()),
                request.getInvocationMethod().trim(),
                user.id(),
                "PENDING",
                defaultText(request.getSource(), "manual"),
                defaultText(request.getSourceUrl(), ""),
                defaultText(request.getSourceAuthor(), user.name()),
                defaultText(request.getLicense(), "Unknown"),
                defaultText(request.getOperatingSystem(), "Cloud / API")
        );
        skillRepository.save(skill);
        return toSkillResponse(skill, "", "");
    }

    public List<UserResponse> getUsers() {
        return userAccountRepository.findAll().stream()
                .map(user -> new UserResponse(user.id(), user.name(), user.email(), user.role()))
                .toList();
    }

    public UserProfileResponse getUserProfile(String userId) {
        UserAccount user = requireAuthenticatedUser(userId);
        List<Skill> allSkills = skillRepository.findAll();
        List<SkillResponse> submittedSkills = allSkills.stream()
                .filter(skill -> user.id().equals(skill.getSubmittedBy()))
                .sorted(Comparator.comparingInt((Skill skill) -> recommendationScore(skill, "", "")).reversed())
                .map(skill -> toSkillResponse(skill, "", ""))
                .toList();
        Map<String, Skill> skillMap = allSkills.stream()
                .collect(Collectors.toMap(Skill::getId, skill -> skill, (left, right) -> left));
        List<UserReviewResponse> submittedReviews = reviewRepository.findByUserId(user.id()).stream()
                .sorted(Comparator.comparing(Review::getTimestamp).reversed())
                .map(review -> new UserReviewResponse(
                        review.getId(),
                        review.getSkillId(),
                        skillMap.containsKey(review.getSkillId()) ? skillMap.get(review.getSkillId()).getName() : review.getSkillId(),
                        review.getRating(),
                        review.getComment(),
                        review.getTimestamp()
                ))
                .toList();
        return new UserProfileResponse(
                new UserResponse(user.id(), user.name(), user.email(), user.role()),
                submittedSkills,
                submittedReviews
        );
    }

    public List<SkillResponse> getPendingSkills(String adminUserId) {
        requireAdmin(adminUserId);
        return skillRepository.findAll().stream()
                .filter(skill -> "PENDING".equalsIgnoreCase(skill.getApprovalStatus()))
                .map(skill -> toSkillResponse(skill, "", ""))
                .toList();
    }

    @Transactional
    public SkillResponse approveSkill(String adminUserId, String skillId) {
        requireAdmin(adminUserId);
        Skill skill = findSkill(skillId);
        skill.setApprovalStatus("APPROVED");
        skillRepository.save(skill);
        return toSkillResponse(skill, "", "");
    }

    @Transactional
    public SkillResponse adminUpdateSkill(String adminUserId, String skillId, SkillUpdateRequest request) {
        requireAdmin(adminUserId);
        Skill skill = findSkill(skillId);
        skill.update(
                request.getName().trim(),
                request.getCategory().trim(),
                request.getDescription().trim(),
                request.getPricePerCall(),
                request.getStatus().trim(),
                request.getSuccessRate(),
                request.getLatencyP95(),
                request.getCostEfficiency(),
                request.getUserRatingAvg(),
                request.getUserRatingCount(),
                request.getRecentCalls(),
                sanitizeList(request.getFunctions()),
                request.getInvocationMethod().trim(),
                request.getApprovalStatus().trim(),
                defaultText(request.getSource(), skill.getSource()),
                defaultText(request.getSourceUrl(), skill.getSourceUrl()),
                defaultText(request.getSourceAuthor(), skill.getSourceAuthor()),
                defaultText(request.getLicense(), skill.getLicense()),
                defaultText(request.getOperatingSystem(), skill.getOperatingSystem())
        );
        skillRepository.save(skill);
        return toSkillResponse(skill, "", "");
    }

    @Transactional
    public void adminDeleteSkill(String adminUserId, String skillId) {
        requireAdmin(adminUserId);
        reviewRepository.deleteBySkillId(skillId);
        skillRepository.deleteById(skillId);
    }

    public LoginResponse login(LoginRequest request) {
        UserAccount user = userAccountRepository.findByEmailIgnoreCase(request.getEmail().trim())
                .orElseThrow(() -> new UnauthorizedException("Invalid email or password."));
        if (!user.password().equals(request.getPassword())) {
            throw new UnauthorizedException("Invalid email or password.");
        }
        String token = "nexra_" + UUID.randomUUID().toString().replace("-", "");
        sessions.put(token, user.id());
        return new LoginResponse(token, new UserResponse(user.id(), user.name(), user.email(), user.role()));
    }

    @Transactional
    public LoginResponse register(RegisterRequest request) {
        String normalizedEmail = request.getEmail().trim().toLowerCase();
        if (userAccountRepository.existsByEmailIgnoreCase(normalizedEmail)) {
            throw new BadRequestException("This email is already registered.");
        }
        UserAccount user = userAccountRepository.save(new UserAccount(
                "user_" + UUID.randomUUID().toString().replace("-", "").substring(0, 8),
                normalizedEmail,
                request.getPassword(),
                request.getName().trim(),
                "USER"
        ));

        String token = "nexra_" + UUID.randomUUID().toString().replace("-", "");
        sessions.put(token, user.id());
        return new LoginResponse(token, new UserResponse(user.id(), user.name(), user.email(), user.role()));
    }

    public void logout(String authorization) {
        String token = extractBearerToken(authorization);
        if (token != null) {
            sessions.remove(token);
        }
    }

    public String requireAuthenticatedUserId(String authorization) {
        String token = extractBearerToken(authorization);
        if (token != null) {
            String sessionUserId = sessions.get(token);
            if (sessionUserId == null) {
                throw new UnauthorizedException("Session expired. Please sign in again.");
            }
            return sessionUserId;
        }
        throw new UnauthorizedException("Please sign in first.");
    }

    public BillingSummary getBillingSummary() {
        return new BillingSummary(2864.92, 212.08, 0.06);
    }

    public List<BillingTransaction> getTransactions() {
        return List.copyOf(transactions);
    }

    public List<ApiKeyRecord> getApiKeys() {
        return List.copyOf(apiKeys);
    }

    public ApiKeyRecord createApiKey(ApiKeyCreateRequest request) {
        String scope = request.getScope() == null || request.getScope().isBlank() ? "skills:read" : request.getScope().trim();
        ApiKeyRecord created = new ApiKeyRecord(
                "nk_live_" + String.format("%02d", apiKeys.size() + 1),
                request.getName().trim(),
                scope,
                "Never",
                "active"
        );
        apiKeys.add(0, created);
        return created;
    }

    private Skill findSkill(String id) {
        return skillRepository.findById(id)
                .orElseThrow(() -> new IllegalArgumentException("Skill not found: " + id));
    }

    private UserAccount findUser(String userId) {
        return userAccountRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("User not found: " + userId));
    }

    private UserAccount requireAuthenticatedUser(String userId) {
        return findUser(userId);
    }

    public void requireAdminAuthorization(String authorization) {
        requireAdmin(requireAuthenticatedUserId(authorization));
    }

    private void requireAdmin(String userId) {
        UserAccount user = requireAuthenticatedUser(userId);
        if (!"ADMIN".equalsIgnoreCase(user.role())) {
            throw new ForbiddenException("Admin permission required.");
        }
    }

    private String extractBearerToken(String authorization) {
        if (authorization == null || authorization.isBlank()) {
            return null;
        }
        String prefix = "Bearer ";
        if (!authorization.regionMatches(true, 0, prefix, 0, prefix.length())) {
            throw new UnauthorizedException("Unsupported authorization format.");
        }
        String token = authorization.substring(prefix.length()).trim();
        if (token.isBlank()) {
            throw new UnauthorizedException("Missing bearer token.");
        }
        return token;
    }

    private boolean matchesQuery(Skill skill, String query) {
        if (query == null || query.isBlank()) {
            return true;
        }
        String normalized = query.toLowerCase();
        String searchable = (skill.getName() + " " + skill.getCategory() + " " + skill.getDescription() + " "
                + String.join(" ", skill.getFunctions()) + " " + skill.getInvocationMethod()).toLowerCase();
        return searchable.contains(normalized);
    }

    private boolean matchesFunction(Skill skill, String functionName) {
        if (functionName == null || functionName.isBlank()) {
            return true;
        }
        String normalized = functionName.toLowerCase();
        return skill.getFunctions().stream().anyMatch(item -> item.toLowerCase().contains(normalized));
    }

    private boolean matchesReadiness(Skill skill, String readiness, boolean hideTemplates) {
        String readinessCode = deriveReadinessCode(skill);
        if (hideTemplates && "template".equals(readinessCode)) {
            return false;
        }
        if (readiness == null || readiness.isBlank() || "all".equalsIgnoreCase(readiness)) {
            return true;
        }
        return readinessCode.equalsIgnoreCase(readiness.trim());
    }

    private String deriveReadinessCode(Skill skill) {
        String text = String.join(" ",
                safeText(skill.getName()),
                safeText(skill.getDescription()),
                safeText(skill.getInvocationMethod()),
                String.join(" ", skill.getFunctions()),
                safeText(providerName(skill)),
                safeText(skill.getCategory())
        ).toLowerCase();

        if (text.matches(".*(template|boilerplate|starter|scaffold|example sdk|starter project).*")) {
            return "template";
        }
        if (text.matches(".*(local|filesystem|file storage|ollama|plugin bridge|desktop|install|self-hosted).*")) {
            return "local";
        }
        if (text.matches(".*(token|oauth|api key|slack|mysql|sql server|postgres|database|figma|shopify|jumpseller|aws|azure|gcp).*")) {
            return "credentials";
        }
        return "ready";
    }

    private List<String> sanitizeList(List<String> values) {
        return values.stream()
                .map(String::trim)
                .filter(item -> !item.isBlank())
                .collect(Collectors.toList());
    }

    private SkillResponse toSkillResponse(Skill skill, String query, String functionName) {
        int agentScore = agentScore(skill);
        int matchScore = matchScore(skill, query, functionName);
        int recommendationScore = recommendationScore(skill, query, functionName);
        return new SkillResponse(
                skill.getId(),
                skill.getName(),
                skill.getCategory(),
                skill.getDescription(),
                skill.getPricePerCall(),
                skill.getStatus(),
                skill.getSuccessRate(),
                skill.getLatencyP95(),
                skill.getCostEfficiency(),
                skill.getUserRatingAvg(),
                skill.getUserRatingCount(),
                skill.getRecentCalls(),
                agentScore,
                agentScore,
                normalizedUserRating(skill),
                overallTrust(skill),
                matchScore,
                recommendationScore,
                recommendationSummary(skill, query, functionName),
                skill.getFunctions(),
                skill.getInvocationMethod(),
                skill.getSubmittedBy(),
                skill.getApprovalStatus(),
                skill.getSource(),
                skill.getSourceUrl(),
                skill.getSourceAuthor(),
                skill.getLicense(),
                skill.getOperatingSystem(),
                providerName(skill),
                providerUrl(skill),
                providerUrl(skill),
                authRequirement(skill),
                callExample(skill)
        );
    }

    private ReviewResponse toReviewResponse(Review review) {
        return new ReviewResponse(
                review.getId(),
                review.getSkillId(),
                review.getAuthor(),
                review.getRating(),
                review.getComment(),
                review.getTimestamp()
        );
    }

    private int agentScore(Skill skill) {
        double latencyScore = clamp(100 - (skill.getLatencyP95() - 200) / 10.0, 35, 100);
        return (int) Math.round(skill.getSuccessRate() * 0.5 + latencyScore * 0.3 + skill.getCostEfficiency() * 0.2);
    }

    private int normalizedUserRating(Skill skill) {
        return (int) Math.round((skill.getUserRatingAvg() / 5.0) * 100);
    }

    private int overallTrust(Skill skill) {
        return (int) Math.round(normalizedUserRating(skill) * 0.45 + agentScore(skill) * 0.55);
    }

    private int matchScore(Skill skill, String query, String functionName) {
        boolean noFilters = (query == null || query.isBlank()) && (functionName == null || functionName.isBlank());
        if (noFilters) {
            return 70;
        }
        int score = 0;
        String normalizedQuery = query == null ? "" : query.trim().toLowerCase();
        String normalizedFunction = functionName == null ? "" : functionName.trim().toLowerCase();
        if (!normalizedQuery.isBlank()) {
            if (skill.getName().toLowerCase().contains(normalizedQuery)) {
                score += 40;
            }
            if (skill.getCategory().toLowerCase().contains(normalizedQuery)) {
                score += 15;
            }
            if (skill.getDescription().toLowerCase().contains(normalizedQuery)) {
                score += 20;
            }
            if (skill.getInvocationMethod().toLowerCase().contains(normalizedQuery)) {
                score += 10;
            }
            if (skill.getFunctions().stream().anyMatch(item -> item.toLowerCase().contains(normalizedQuery))) {
                score += 15;
            }
        }
        if (!normalizedFunction.isBlank()) {
            if (skill.getFunctions().stream().anyMatch(item -> item.equalsIgnoreCase(normalizedFunction))) {
                score += 35;
            } else if (skill.getFunctions().stream().anyMatch(item -> item.toLowerCase().contains(normalizedFunction))) {
                score += 25;
            } else if (skill.getDescription().toLowerCase().contains(normalizedFunction)) {
                score += 15;
            }
        }
        return (int) clamp(score, 0, 100);
    }

    private int recommendationScore(Skill skill, String query, String functionName) {
        double popularity = clamp(Math.log10(skill.getRecentCalls() + 10) * 20, 20, 100);
        return (int) Math.round(
                matchScore(skill, query, functionName) * 0.35
                        + overallTrust(skill) * 0.35
                        + popularity * 0.15
                        + skill.getCostEfficiency() * 0.10
                        + skill.getSuccessRate() * 0.05
        );
    }

    private String recommendationSummary(Skill skill, String query, String functionName) {
        List<String> reasons = new ArrayList<>();
        if (matchScore(skill, query, functionName) >= 75) {
            reasons.add("strong capability match");
        }
        if (overallTrust(skill) >= 85) {
            reasons.add("high trust");
        }
        if (skill.getRecentCalls() >= 10000) {
            reasons.add("popular in recent usage");
        }
        if (skill.getCostEfficiency() >= 80) {
            reasons.add("good cost efficiency");
        }
        if (reasons.isEmpty()) {
            reasons.add("balanced trust and coverage");
        }
        return String.join(", ", reasons);
    }

    private String providerName(Skill skill) {
        if (skill.getSourceAuthor() != null && !skill.getSourceAuthor().isBlank()) {
            return skill.getSourceAuthor();
        }
        return skill.getSubmittedBy();
    }

    private String providerUrl(Skill skill) {
        return skill.getSourceUrl() == null ? "" : skill.getSourceUrl();
    }

    private String authRequirement(Skill skill) {
        String invocation = skill.getInvocationMethod().toLowerCase();
        if (invocation.contains("local")) {
            return "Requires local runtime setup. Check provider docs for installation steps.";
        }
        if (providerUrl(skill).isBlank()) {
            return "Check the provider before use. Authentication requirements are not documented in Nexra yet.";
        }
        return "Review the provider documentation for API key, OAuth, or local runtime requirements before calling.";
    }

    private String callExample(Skill skill) {
        String function = skill.getFunctions().isEmpty() ? "task" : skill.getFunctions().get(0);
        return "{ \"task\": \"" + function + "\", \"skill\": \"" + skill.getName() + "\", \"notes\": \"Call this provider directly after choosing it in Nexra.\" }";
    }

    private String defaultText(String value, String fallback) {
        return value == null || value.isBlank() ? fallback : value.trim();
    }

    private String safeText(String value) {
        return value == null ? "" : value;
    }

    private double clamp(double value, double min, double max) {
        return Math.min(Math.max(value, min), max);
    }
}
