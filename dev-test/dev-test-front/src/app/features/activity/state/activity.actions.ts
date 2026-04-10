import { createAction, props } from '@ngrx/store';
import { Activity } from '../../activity/model/activity';
import { FilterActivity } from '../../activity/model/activity-filterdata';

const SetFilter = createAction(
    '[Activity] Set Filter',
    props<{ filterActivity: FilterActivity }>()
);

const SelectActivity = createAction(
  '[Activity] Select Activity',
    props<{ activity: Activity }>()
);

export { SetFilter, SelectActivity };
