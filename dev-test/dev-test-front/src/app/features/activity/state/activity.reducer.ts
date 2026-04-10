import {Action, createReducer, on} from '@ngrx/store';
import * as ActivityAction from './activity.actions';
import { FilterActivity } from '../../activity/model/activity-filterdata';
import { Activity } from '../../activity/model/activity';

export interface State {
    filterActivity: FilterActivity;
    activity: Activity;
}

export const initialState: State = {
    filterActivity: {},
    activity: {}
} as State;

const ActivityReducer = createReducer(
  initialState,
  on(ActivityAction.SetFilter, (state, { filterActivity }) => ({ ...state, filterActivity })),
  on(ActivityAction.SelectActivity, (state, { activity }) => ({ ...state, activity })),
);

export function reducerActivity(state: State | undefined, action: Action) {
    return ActivityReducer(state, action);
}
