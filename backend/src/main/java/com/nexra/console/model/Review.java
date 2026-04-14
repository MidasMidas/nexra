package com.nexra.console.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "reviews")
public class Review {
    @Id
    private String id;

    @Column(nullable = false)
    private String skillId;
    private String userId;
    private String author;
    private int rating;

    @Column(columnDefinition = "TEXT")
    private String comment;
    private String timestamp;

    public Review() {
    }

    public Review(String id, String skillId, String userId, String author, int rating, String comment, String timestamp) {
        this.id = id;
        this.skillId = skillId;
        this.userId = userId;
        this.author = author;
        this.rating = rating;
        this.comment = comment;
        this.timestamp = timestamp;
    }

    public String getId() {
        return id;
    }

    public String getSkillId() {
        return skillId;
    }

    public String getUserId() {
        return userId;
    }

    public String getAuthor() {
        return author;
    }

    public int getRating() {
        return rating;
    }

    public String getComment() {
        return comment;
    }

    public String getTimestamp() {
        return timestamp;
    }
}
