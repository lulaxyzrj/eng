package br.com.engdb.dev.resource;

import br.com.engdb.dev.dto.TaskDto;
import br.com.engdb.dev.service.TaskService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping(value = "/api/tasks/")
public class TaskResource {

    private final TaskService service;

    @Autowired
    public TaskResource(TaskService service) {
        this.service = service;
    }

    @GetMapping
    public ResponseEntity<List<TaskDto>> getAll() {
        return new ResponseEntity<>(service.getAll(), HttpStatus.OK);
    }

    @GetMapping("/{id}")
    public ResponseEntity<TaskDto> getById(@PathVariable("id") Long id) {
        return new ResponseEntity<>(service.getById(id), HttpStatus.OK);
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public ResponseEntity<TaskDto> create(@RequestBody TaskDto task) {
        return new ResponseEntity<>(service.create(task), HttpStatus.OK);
    }

    @PutMapping("/{id}")
    public ResponseEntity<TaskDto> updateTask(@PathVariable("id") Long id, @RequestBody TaskDto task) {
        return new ResponseEntity<>(service.update(task), HttpStatus.OK);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteTask(@PathVariable("id") Long id) {
        service.delete(id);
    }

    @PutMapping("/setInactive")
    public ResponseEntity<TaskDto> setInactive(@RequestBody Long id) {
        TaskDto result = service.setActive(id, false);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

    @PutMapping(value = "/setActive")
    public ResponseEntity<TaskDto> setActive(@RequestBody Long id) {
        TaskDto result = service.setActive(id, true);
        return new ResponseEntity<>(result, HttpStatus.OK);
    }

}
