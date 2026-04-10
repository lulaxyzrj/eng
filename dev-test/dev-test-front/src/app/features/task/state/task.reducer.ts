import {Action, createReducer, on} from '@ngrx/store';
import * as TaskAction from './task.actions';
import { FilterTask } from '../model/task-filterdata';
import { Task } from '../model/task';

export interface State {
    filterTask: FilterTask;
    task: Task;
}

export const initialState: State = {
    filterTask: {},
    task: {}
} as State;

const TaskReducer = createReducer(
  initialState,
  on(TaskAction.SetFilter, (state, { filterTask }) => ({ ...state, filterTask })),
  on(TaskAction.SelectTask, (state, { task }) => ({ ...state, task })),
);

export function reducerTask(state: State | undefined, action: Action) {
    return TaskReducer(state, action);
}
