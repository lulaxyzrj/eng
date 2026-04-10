package br.com.engdb.dev.service.impl;

import br.com.engdb.dev.domain.Task;
import br.com.engdb.dev.dto.TaskDto;
import br.com.engdb.dev.exception.CustomException;
import br.com.engdb.dev.mapper.TaskMapper;
import br.com.engdb.dev.repository.TaskRepository;
import br.com.engdb.dev.service.TaskService;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class TaskServiceImpl implements TaskService {

    private final TaskRepository repository;
    private final TaskMapper mapper;

    @Autowired
    public TaskServiceImpl(TaskRepository repository, TaskMapper mapper) {
        this.repository = repository;
        this.mapper = mapper;
    }

    @Override
    public List<TaskDto> getAll() {
        return mapper.toDtoList(repository.findAll());
    }

    @Override
    public TaskDto getById(Long id) {
        return mapper.toDto(repository.findById(id).orElseThrow());
    }

    @Override
    public TaskDto create(TaskDto task) {
        if (task.getName() == null || task.getName().isEmpty()) {
            throw new CustomException("error.emptyName");
        }
        Task entity = mapper.toEntity(task);
        entity = repository.save(entity);
        return mapper.toDto(entity);
    }

    @Override
    public TaskDto update(TaskDto task) {
        if (task.getName() == null || task.getName().isEmpty()) {
            throw new CustomException("error.emptyName");
        }
        Task entity = mapper.toEntity(task);
        entity = repository.save(entity);
        return mapper.toDto(entity);
    }

    @Override
    public void delete(Long id) {
        repository.deleteById(id);
    }

    @Override
    public TaskDto setActive(Long id, boolean active) {
        Task task = repository.findById(id).orElseThrow();
        task.setActive(active);
        task = repository.save(task);
        return mapper.toDto(task);
    }

    @PostConstruct
    private void populateDataBase() {
        for (long i=1; i<3; i++) {
            Task task = new Task();
            task.setName("Tarefa " + i);
            task.setDescription("Descrição da tarefa " + i);
            task.setActive(true);
            repository.save(task);
        }
    }
}
