import {Injectable} from '@angular/core';
import {createFeatureSelector, createSelector} from '@ngrx/store';
import {initialState, State} from './task.reducer';
import { TaskEntityService } from '../service/task-entity.service';
import { Task } from '../model/task';

const getTaskState = createFeatureSelector<State>('Task');

@Injectable()
export class TaskSelectors {

    selectFilter = createSelector(
        getTaskState, (state: State) => state ? state.filterTask : initialState.filterTask);

    allTask = createSelector(
        this.taskEntityService.selectors.selectEntities,
        TaskTypes => {
            return TaskTypes;
        }
    );

    selectTask = createSelector(
        this.selectFilter,
        this.taskEntityService.selectors.selectEntityMap,
        (filterData, task) => filterData ? task[filterData.id] : {} as Task
    );

    constructor(
        private taskEntityService: TaskEntityService) {
    }

}
