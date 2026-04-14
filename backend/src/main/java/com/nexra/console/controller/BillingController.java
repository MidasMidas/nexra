package com.nexra.console.controller;

import com.nexra.console.model.BillingSummary;
import com.nexra.console.model.BillingTransaction;
import com.nexra.console.service.NexraService;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/billing")
@CrossOrigin(origins = "*")
public class BillingController {
    private final NexraService nexraService;

    public BillingController(NexraService nexraService) {
        this.nexraService = nexraService;
    }

    @GetMapping("/summary")
    public BillingSummary getSummary(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.getBillingSummary();
    }

    @GetMapping("/transactions")
    public List<BillingTransaction> getTransactions(@RequestHeader(value = "Authorization", required = false) String authorization) {
        nexraService.requireAuthenticatedUserId(authorization);
        return nexraService.getTransactions();
    }
}
