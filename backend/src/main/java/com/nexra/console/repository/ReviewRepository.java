package com.nexra.console.repository;

import com.nexra.console.model.Review;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ReviewRepository extends JpaRepository<Review, String> {
    List<Review> findBySkillId(String skillId);
    List<Review> findByUserId(String userId);
    void deleteBySkillId(String skillId);
}
