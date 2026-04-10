package br.com.engdb.dev.service.impl;

import br.com.engdb.dev.builders.dto.TaskDtoBuilder;
import br.com.engdb.dev.builders.model.TaskBuilder;
import br.com.engdb.dev.domain.Task;
import br.com.engdb.dev.dto.TaskDto;
import br.com.engdb.dev.mapper.TaskMapper;
import br.com.engdb.dev.repository.TaskRepository;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.*;

import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;

class TaskServiceImplTest {

    @Mock
    private TaskRepository repository;

    @Mock
    private TaskMapper mapper;

    @InjectMocks
    private TaskServiceImpl taskService;

    private AutoCloseable closeable;

    @BeforeEach
    public void setup() {
        closeable = MockitoAnnotations.openMocks(this);
    }

    @AfterEach
    public void tearDown() throws Exception {
        closeable.close();
    }

    @Test
    void getAll() {
        List<Task> entityList = Collections.singletonList(TaskBuilder.one().now());
        List<TaskDto> dtoList = Collections.singletonList(TaskDtoBuilder.one().now());
        Mockito.when(repository.findAll()).thenReturn(entityList);
        Mockito.when(mapper.toDtoList(entityList)).thenReturn(dtoList);

        List<TaskDto> result = taskService.getAll();

        assertEquals(1L, result.size());
        assertEquals(result.getFirst().getId(), entityList.getFirst().getId());
        assertEquals(result.getFirst().getName(), entityList.getFirst().getName());
    }

    @Test
    void create() {
        Task entity = TaskBuilder.one().now();
        TaskDto dto = TaskDtoBuilder.one().now();
        dto.setId(null);
        Mockito.when(mapper.toEntity(dto)).thenReturn(entity);
        Mockito.when(mapper.toDto(entity)).thenReturn(dto);

        taskService.create(dto);

        ArgumentCaptor<Task> argumentCaptor = ArgumentCaptor.forClass(Task.class);
        Mockito.verify(repository, Mockito.times(1)).save(argumentCaptor.capture());
        assertEquals(dto.getName(), argumentCaptor.getValue().getName());
    }

    @Test
    void delete() {
        taskService.delete(1L);

        ArgumentCaptor<Long> argumentCaptor = ArgumentCaptor.forClass(Long.class);
        Mockito.verify(repository, Mockito.times(1)).deleteById(argumentCaptor.capture());
        assertEquals(1L, argumentCaptor.getValue());
    }

}