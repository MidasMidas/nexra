package com.nexra.console.controller;

import com.nexra.console.dto.MessageResponse;
import com.nexra.console.service.BadRequestException;
import com.nexra.console.service.ForbiddenException;
import com.nexra.console.service.UnauthorizedException;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public MessageResponse handleIllegalArgument(IllegalArgumentException exception) {
        return new MessageResponse(exception.getMessage());
    }

    @ExceptionHandler(BadRequestException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MessageResponse handleBadRequest(BadRequestException exception) {
        return new MessageResponse(exception.getMessage());
    }

    @ExceptionHandler(UnauthorizedException.class)
    @ResponseStatus(HttpStatus.UNAUTHORIZED)
    public MessageResponse handleUnauthorized(UnauthorizedException exception) {
        return new MessageResponse(exception.getMessage());
    }

    @ExceptionHandler(ForbiddenException.class)
    @ResponseStatus(HttpStatus.FORBIDDEN)
    public MessageResponse handleForbidden(ForbiddenException exception) {
        return new MessageResponse(exception.getMessage());
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public MessageResponse handleValidation(MethodArgumentNotValidException exception) {
        return new MessageResponse("Invalid request: " + exception.getBindingResult().getErrorCount() + " validation error(s).");
    }
}
