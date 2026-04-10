package br.com.engdb.dev.mapper;

import br.com.engdb.dev.domain.Task;
import br.com.engdb.dev.dto.TaskDto;
import java.util.ArrayList;
import java.util.List;
import javax.annotation.processing.Generated;
import org.springframework.stereotype.Component;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2026-02-06T13:45:01-0300",
    comments = "version: 1.6.3, compiler: Eclipse JDT (IDE) 3.45.0.v20260128-0750, environment: Java 21.0.9 (Eclipse Adoptium)"
)
@Component
public class TaskMapperImpl implements TaskMapper {

    @Override
    public TaskDto toDto(Task entity) {
        if ( entity == null ) {
            return null;
        }

        TaskDto taskDto = new TaskDto();

        taskDto.setId( entity.getId() );
        taskDto.setName( entity.getName() );
        taskDto.setDescription( entity.getDescription() );
        taskDto.setActive( entity.isActive() );

        return taskDto;
    }

    @Override
    public List<TaskDto> toDtoList(List<Task> entityList) {
        if ( entityList == null ) {
            return null;
        }

        List<TaskDto> list = new ArrayList<TaskDto>( entityList.size() );
        for ( Task task : entityList ) {
            list.add( toDto( task ) );
        }

        return list;
    }

    @Override
    public Task toEntity(TaskDto entity) {
        if ( entity == null ) {
            return null;
        }

        Task task = new Task();

        task.setId( entity.getId() );
        task.setName( entity.getName() );
        task.setDescription( entity.getDescription() );
        task.setActive( entity.isActive() );

        return task;
    }

    @Override
    public List<Task> toEntityList(List<TaskDto> entityList) {
        if ( entityList == null ) {
            return null;
        }

        List<Task> list = new ArrayList<Task>( entityList.size() );
        for ( TaskDto taskDto : entityList ) {
            list.add( toEntity( taskDto ) );
        }

        return list;
    }
}
