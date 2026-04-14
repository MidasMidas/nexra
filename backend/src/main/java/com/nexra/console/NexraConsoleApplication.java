package com.nexra.console;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
@EnableJpaRepositories(basePackages = "com.nexra.console.repository")
@EntityScan(basePackages = "com.nexra.console.model")
public class NexraConsoleApplication {

    public static void main(String[] args) {
        SpringApplication.run(NexraConsoleApplication.class, args);
    }
}
