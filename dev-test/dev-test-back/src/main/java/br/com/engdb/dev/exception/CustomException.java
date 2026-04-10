package br.com.engdb.dev.exception;

public class CustomException extends RuntimeException{
    private final String message;

    public CustomException(String message) {
        this.message = message;
    }
}
