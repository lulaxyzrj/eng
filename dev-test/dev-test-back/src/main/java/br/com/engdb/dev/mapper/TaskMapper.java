package br.com.engdb.dev.mapper;

import br.com.engdb.dev.domain.Task;
import br.com.engdb.dev.dto.TaskDto;
import org.mapstruct.Mapper;

import java.util.List;

@Mapper(componentModel = "spring")
public interface TaskMapper {
    TaskDto toDto(Task entity);
    List<TaskDto> toDtoList(List<Task> entityList);
    Task toEntity(TaskDto entity);
    List<Task> toEntityList(List<TaskDto> entityList);
}
