package br.com.engdb.dev.service;

import br.com.engdb.dev.dto.TaskDto;

import java.util.List;

public interface TaskService {
    List<TaskDto> getAll();
    TaskDto getById(Long id);
    TaskDto create(TaskDto task);
    TaskDto update(TaskDto task);
    void delete(Long id);
    TaskDto setActive(Long id, boolean b);
}
