import {Injectable} from '@angular/core';
import {Store} from '@ngrx/store';
import {State} from './task.reducer';
import {SelectTask, SetFilter} from './task.actions';
import { FilterTask } from '../model/task-filterdata';
import { Task } from '../model/task';

@Injectable()
export class TaskDispatchers {
    constructor(private store: Store<State>) {
    }

    setFilter(filterTask: FilterTask) {
        this.store.dispatch(SetFilter({filterTask}));
    }

    selectTask(task: Task) {
        this.store.dispatch(SelectTask({task}));
    }

}
