package br.com.engdb.dev.builders.model;


import br.com.engdb.dev.domain.Task;

public class TaskBuilder {

    private Task element;

    private TaskBuilder(){}

    public static TaskBuilder one() {
        TaskBuilder builder = new TaskBuilder();
        initDefaultData(builder);
        return builder;
    }

    public static void initDefaultData(TaskBuilder builder) {
        builder.element = new Task();
        builder.element.setId(1L);
        builder.element.setName("Task 1");
        builder.element.setDescription("Description task 1");
        builder.element.setActive(true);
    }

    public Task now() {
        return element;
    }
}
