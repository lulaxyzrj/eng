import { createAction, props } from '@ngrx/store';
import { FilterTask } from '../model/task-filterdata';
import { Task } from '../model/task';

const SetFilter = createAction(
    '[Task] Set Filter',
    props<{ filterTask: FilterTask }>()
);

const SelectTask = createAction(
  '[Task] Select Task',
    props<{ task: Task }>()
);

export { SetFilter, SelectTask };
