package com.nexra.console;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class NexraConsoleApplication {

    public static void main(String[] args) {
        SpringApplication.run(NexraConsoleApplication.class, args);
    }
}
