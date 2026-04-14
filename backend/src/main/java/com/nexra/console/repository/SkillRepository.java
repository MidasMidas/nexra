package com.nexra.console.repository;

import com.nexra.console.model.Skill;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SkillRepository extends JpaRepository<Skill, String> {
    long countBySubmittedByIgnoreCase(String submittedBy);
}
