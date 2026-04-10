package br.com.engdb.dev.builders.dto;

import br.com.engdb.dev.dto.TaskDto;

public class TaskDtoBuilder {

    private TaskDto element;

    private TaskDtoBuilder(){}

    public static TaskDtoBuilder one() {
        TaskDtoBuilder builder = new TaskDtoBuilder();
        initDefaultData(builder);
        return builder;
    }

    public static void initDefaultData(TaskDtoBuilder builder) {
        builder.element = new TaskDto();
        builder.element.setId(1L);
        builder.element.setName("Task 1");
        builder.element.setDescription("Description task 1");
        builder.element.setActive(true);
    }

    public TaskDto now() {
        return element;
    }
}
